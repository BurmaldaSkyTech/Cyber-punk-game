"""Типизированный доступ к боевым правилам книги. Сырые значения лежат в
data/rules/combat.json (включая строки-формулы), парсинг — здесь."""
import math
import random
import re

from backend import rules

HOUSE_AIMED = -8
HOUSE_MULT = {"head": 2}
HOUSE_WOUND = {"lightly": 0, "seriously": -2, "mortally": -4}
HOUSE_MOVE_PEN = -6

WEAPON_ROW = {
    "medium_pistol": "pistol", "heavy_pistol": "pistol", "very_heavy_pistol": "pistol",
    "smg": "smg", "heavy_smg": "smg", "shotgun": "shotgun_slug",
    "assault_rifle": "assault_rifle", "sniper_rifle": "sniper_rifle",
    "grenade_launcher": "grenade_launcher", "rocket_launcher": "rocket_launcher",
    "bow": "bows_crossbow", "crossbow": "bows_crossbow",
}


def _raw(key, default=None):
    return rules.get_optional("combat", key, default)


def _num(v, default=None):
    if isinstance(v, (int, float)):
        return int(v)
    m = re.search(r"-?\d+", str(v or ""))
    return int(m.group()) if m else default


def aimed_penalty(location):
    if location not in ("head", "limb"):
        return 0
    v = _raw("aimed_shot_penalties")
    if isinstance(v, dict):
        for k, x in v.items():
            if k.strip().lower() == location:
                return _num(x, HOUSE_AIMED)
        return 0
    return _num(v, HOUSE_AIMED)


def aimed_multiplier(location):
    v = _raw("aimed_shot_multipliers")
    if isinstance(v, dict):
        for k, x in v.items():
            if k.strip().lower() == location:
                return _num(x, 1) or 1
    return HOUSE_MULT.get(location, 1)


def aimed_costs_full_action(location):
    return location in ("head", "limb")


def ablation_step():
    v = _raw("armor_ablation")
    if isinstance(v, (int, float)):
        return int(v)
    m = re.search(r"by\s+(\d+)", str(v or ""), re.I)
    return int(m.group(1)) if m else 1


def crit_trigger():
    v = _raw("critical_injury_trigger")
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v or "").lower()
    if "two" in s:
        return 2
    return _num(v, 2)


def crit_bonus():
    return _num(_raw("critical_injury_bonus"), 5)


def wound_state(hp, max_hp):
    hp, max_hp = int(hp), max(1, int(max_hp))
    if hp < 1:
        return "mortally"
    if hp < math.ceil(max_hp / 2):
        return "seriously"
    if hp < max_hp:
        return "lightly"
    return "unharmed"


def _wound_entry(state):
    v = _raw("wound_penalties")
    if isinstance(v, dict):
        for k, x in v.items():
            if k.strip().lower().startswith(state):
                return str(x)
    return None


def wound_penalty(state, stat_key=None):
    if state == "unharmed":
        return 0
    txt = _wound_entry(state)
    if txt is None:
        base = HOUSE_WOUND.get(state, 0)
        if state == "mortally" and stat_key == "MOVE":
            return HOUSE_MOVE_PEN
        return base
    if "none" in txt.lower():
        return 0
    if stat_key == "MOVE":
        m = re.search(r"(-\d+)\s*to MOVE", txt, re.I)
        if m:
            return int(m.group(1))
    m = re.search(r"(-\d+)\s*to all", txt, re.I)
    return int(m.group(1)) if m else HOUSE_WOUND.get(state, 0)


def death_save(entity):
    """d10 под BODY с накопительным штрафом; 10 — всегда провал."""
    body = int((entity.get("stats") or {}).get("BODY", 4))
    pen = int(entity.get("death_save_penalty", 0))
    die = random.randint(1, 10)
    total = die + pen
    dead = (die == 10) or (total >= body)
    entity["death_save_penalty"] = pen + 1
    if dead:
        entity["dead"] = True
    return {"roll": die, "penalty": pen, "total": total, "body": body, "dead": dead}


def _range_row(weapon_key):
    table = _raw("range_dv")
    if not isinstance(table, dict):
        return None
    want = WEAPON_ROW.get(weapon_key, weapon_key)
    for k, bands in table.items():
        norm = re.sub(r"[^a-z0-9]+", "_", k.strip().lower()).strip("_")
        if norm == want or norm.startswith(want.split("_")[0]):
            return bands
    return None


def range_dv(weapon_key, distance=3):
    bands = _range_row(weapon_key)
    if not isinstance(bands, dict):
        return None
    for band, dv in bands.items():
        m = re.match(r"\s*(\d+)\s*-\s*(\d+)", str(band))
        if m and int(m.group(1)) <= distance <= int(m.group(2)):
            return int(dv)
    return None


def dodge_dv(defender):
    """Защита от дальнего боя: уклонение доступно только при REF >= 8."""
    if int((defender.get("stats") or {}).get("REF", 0)) < 8:
        return None
    dex = int((defender.get("stats") or {}).get("DEX", 4))
    ev = int((defender.get("skills") or {}).get("evasion", 0))
    return random.randint(1, 10) + dex + ev


def melee_defense(defender):
    dex = int((defender.get("stats") or {}).get("DEX", 4))
    ev = int((defender.get("skills") or {}).get("evasion", 0))
    return random.randint(1, 10) + dex + ev


def crit_injury(location, roll_total):
    key = "critical_injury_table_head" if location == "head" else "critical_injury_table_body"
    table = rules.get_optional("combat", key)
    if isinstance(table, dict):
        return table.get(str(roll_total))
    return None


def autofire_damage(margin, rating):
    if not rating:
        return None
    mult = max(1, min(int(margin), int(rating)))
    return sum(random.randint(1, 6) for _ in range(2)) * mult