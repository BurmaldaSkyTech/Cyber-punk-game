# backend/engine.py
import json, random, re
from pathlib import Path
from . import db
# Загрузка полных данных из файлов
import json
from pathlib import Path

_data_dir = Path(__file__).parent.parent / "data" / "normalized"

def _load_json(filename, default=None):
    path = _data_dir / filename
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}

SKILLS_FULL = _load_json("skills_full.json", {})
WEAPONS_FULL = _load_json("weapons_full.json", {})
ARMOR_FULL = _load_json("armor_full.json", {})
CYBERWARE_FULL = _load_json("cyberware_full.json", {})

# Обновление карты статов на основе полного списка навыков
for skill_name, skill_data in SKILLS_FULL.items():
    SKILL_STAT[skill_name] = skill_data["stat"]

RULES = Path(__file__).resolve().parent.parent / "data" / "rules"


def _load(name, default):
    p = RULES / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


DV = {str(r.get("level", "")).lower(): int(r["dv"])
      for r in db.family_rows("dv_table")
      if r.get("dv") is not None and str(r.get("dv")).lstrip("-").isdigit()} \
     or _load("dv.json", {"simple": 9, "everyday": 13, "difficult": 15,
                          "professional": 17, "heroic": 21, "incredible": 24, "legendary": 29})
WEAPONS = db.family_map("weapons") or _load("weapons.json", {})
ARMOR = db.family_map("armor") or _load("armor.json", {})

WOUND_MOD = {"unharmed": 0, "lightly": 0, "seriously": -2, "mortally": -4}

SKILL_STAT = {
    "handgun": "REF", "shoulder_arms": "REF", "autofire": "REF",
    "melee": "DEX", "melee_weapon": "DEX", "evasion": "DEX", "stealth": "DEX",
    "athletics": "BODY", "drive": "REF", "perception": "INT", "deduction": "INT",
    "interface": "INT", "programming": "TECH", "electronics": "TECH", "basic_tech": "TECH",
    "persuasion": "EMP", "conversation": "EMP", "human_perception": "EMP",
    "streetwise": "INT", "first_aid": "INT", "paramedic": "TECH",
}

SKILL_STAT.update({
    # INT
    "accounting": "INT", "conceal_reveal_object": "INT", "criminology": "INT",
    "cryptography": "INT", "deduction": "INT", "education": "INT",
    "gamble": "INT", "language": "INT", "library_search": "INT",
    "lip_reading": "INT", "local_expert": "INT", "perception": "INT",
    "science": "INT", "tactics": "INT", "tracking": "INT",
    "wilderness_survival": "INT", "interface": "INT", "programming": "INT",
    
    # REF
    "brawling": "REF", "contortionist": "REF", "dance": "REF",
    "drive_land_vehicle": "REF", "drive_sea_vehicle": "REF", "evasion": "REF",
    "handgun": "REF", "heavy_weapons": "REF", "martial_arts": "REF",
    "melee_weapon": "REF", "pilot_air_vehicle": "REF", "pilot_sea_vehicle": "REF",
    "riding": "REF", "shoulder_arms": "REF", "stealth": "REF",
    
    # TECH
    "air_vehicle_tech": "TECH", "basic_tech": "TECH", "cybertech": "TECH",
    "demolitions": "TECH", "electronics_security_tech": "TECH", "first_aid": "TECH",
    "forgery": "TECH", "land_vehicle_tech": "TECH", "paint_draw_photography": "TECH",
    "paramedic": "TECH", "pharmaceuticals": "TECH", "pick_lock": "TECH",
    "pick_pocket": "TECH", "sea_vehicle_tech": "TECH", "weaponstech": "TECH",
    
    # COOL
    "acting": "COOL", "bribery": "COOL", "conversation": "COOL",
    "human_perception": "COOL", "interrogation": "COOL", "persuasion": "COOL",
    "personal_grooming": "COOL", "streetwise": "COOL", "trading": "COOL",
    "wardrobe_style": "COOL",
    
    # EMP
    "performance": "EMP",
    
    # WILL
    "concentration": "WILL", "endurance": "WILL", "resist_torture_drugs": "WILL",
    
    # BODY
    "athletics": "BODY",
    
    # MOVE
    "stealth_move": "MOVE",
})

def roll_d10():
    first = random.randint(1, 10)
    total = first
    if first == 10:
        while True:
            d = random.randint(1, 10); total += d
            if d != 10: break
    elif first == 1:
        while True:
            d = random.randint(1, 10); total -= d
            if d != 1: break
    return first, total


def roll_dice(expr):
    m = re.fullmatch(r"(\d+)d(\d+)([+-]\d+)?", expr.replace(" ", "").lower())
    if not m:
        return 0, []
    n, sides, mod = int(m[1]), int(m[2]), int(m[3] or 0)
    faces = [random.randint(1, sides) for _ in range(n)]
    return sum(faces) + mod, faces


def skill_check(stat, skill, dv, mods=0):
    first, die = roll_d10()
    total = stat + skill + die + mods
    return {"dice": first, "die_total": die, "stat": stat, "skill": skill,
            "mods": mods, "total": total, "dv": dv, "success": total >= dv,
            "margin": total - dv, "critical": first == 10, "fumble": first == 1}


def wound_state(hp, max_hp):
    half = -(-max_hp // 2)
    if hp < 1: return "mortally"
    if hp < half: return "seriously"
    if hp < max_hp: return "lightly"
    return "unharmed"


def apply_damage(target, amount):
    target["hp"] -= amount
    target["wound"] = wound_state(target["hp"], target["max_hp"])
    return target


def death_save(target):
    first, _ = roll_d10()
    roll = first + target.get("dsp", 0)
    alive = (first != 10) and (roll < target["stats"]["BODY"])
    if alive:
        target["dsp"] = target.get("dsp", 0) + 1
    else:
        target["dead"] = True
    return {"roll": first, "with_penalty": roll, "body": target["stats"]["BODY"], "alive": alive}


def resolve_check(state, actor, judge):
    # Free-действия: без броска
    if judge.get("action_type") == "free":
        return {
            "dice": None, "die_total": None, "stat": None, "skill": None,
            "mods": 0, "total": None, "dv": None, "success": True,
            "margin": 0, "critical": False, "fumble": False,
            "actor": actor["name"], "action_type": "free",
            "skill": "", "stat_key": None, "dv_key": None, "no_roll": True,
        }
    dv_key = judge.get("dv_key", "everyday")
    dv = judge.get("dv") or DV.get(dv_key, 13)
    skill = judge.get("skill") or ""
    stat_key = SKILL_STAT.get(skill, judge.get("stat", "COOL"))
    stat = actor["stats"].get(stat_key, 2)
    sk_lvl = actor["skills"].get(skill, 0)
    mods = WOUND_MOD.get(actor.get("wound", "unharmed"), 0)
    mech = skill_check(stat, sk_lvl, dv, mods)
    mech.update({"actor": actor["name"], "action_type": judge.get("action_type", "skill"),
                 "skill": skill, "stat_key": stat_key, "dv_key": dv_key})

    at = mech["action_type"]
    if at == "attack_ranged" and not judge.get("weapon"):
        judge["weapon"] = "heavy_pistol"
    if at == "attack_melee" and not judge.get("weapon"):
        judge["weapon"] = "knife"

    target = None
    if judge.get("target"):
        target = next((n for n in state["npcs"] if n["id"] == judge.get("target")), None)
    if target is None and at in ("attack_ranged", "attack_melee"):
        low = (judge.get("_text") or "").lower()
        target = next((n for n in state["npcs"] if n["name"].lower() in low), None)
        if target is None:
            target = next((n for n in state["npcs"] if n["id"] == state.get("threat")), None)
        if target is None and state["npcs"]:
            target = state["npcs"][0]

    if at in ("attack_ranged", "attack_melee") and mech["success"]:
        wkey = judge.get("weapon", "heavy_pistol")
        w = WEAPONS.get(wkey, {"damage": "2d6"})
        dmg, faces = roll_dice(w["damage"])
        sixes = sum(1 for f in faces if f == 6)
        crit = sixes >= 2
        sp = ARMOR.get((target or {}).get("armor", "leathers"), {}).get("sp", 0) if target else 0
        net = max(0, dmg - sp)
        mech.update({"weapon": wkey, "damage_roll": faces, "damage": dmg,
                     "armor_sp": sp, "net_damage": net,
                     "target": (target or {}).get("name"),
                     "critical_injury": crit, "bonus_damage": 5 if crit else 0})
        if target is not None:
            mech["target_id"] = target["id"]
            if net + (5 if crit else 0) > 0:
                apply_damage(target, net + (5 if crit else 0))
                mech["target_hp"] = target["hp"]
                mech["target_wound"] = target.get("wound", "lightly")
    return mech


def resolve_assist(state, helper, dv, stat_key, skill_key):
    stat = helper["stats"].get(stat_key, 2)
    skill = helper["skills"].get(skill_key, 0)
    res = skill_check(stat, skill, dv)
    if res["success"]:
        return {"helper": helper["name"], "bonus": 2, "result": res}
    state["heat"] = min(10, state["heat"] + 1)
    return {"helper": helper["name"], "bonus": 0, "complication": True, "result": res}
 
COMBAT_FLAGS = {"alerted", "conflict", "pursued", "combat_in_progress",
                "alarm_raised", "bloodbath", "guards_alerted", "guards_aggressive"}

NPC_FALLBACK = {
    "stats": {"REF": 5, "DEX": 4, "BODY": 5, "WILL": 4},
    "skills": {"handgun": 3, "melee": 2},
    "weapon": "heavy_pistol",
    "armor": "kevlar",
}

# Оружие NPC-охраны (по их id из сценария)
NPC_WEAPON = {
    "guard1": "heavy_pistol",
    "guard2": "smg",
}


def resolve_npc_reaction(state, actor, mech):
    """NPC отвечает один раз после действия игрока, если бой уже начался."""
    flags = set(state.get("flags", []))
    if state.get("heat", 0) < 2 and not (flags & COMBAT_FLAGS):
        return None

    npc = next((n for n in state["npcs"] if n["id"] == state.get("threat")), None)
    if npc is None:
        npc = next((n for n in state["npcs"] if n.get("hp", 0) > 0), None)
    if npc is None or npc.get("hp", 0) <= 0 or npc.get("dead"):
        return None

    data = {**NPC_FALLBACK, **npc}
    skill = "melee" if data.get("weapon") in ("knife", "battleglove", "sword", "axe") else "handgun"
    stat_key = SKILL_STAT.get(skill, "REF")
    dv = DV.get("difficult", 15)
    mods = WOUND_MOD.get(npc.get("wound", "unharmed"), 0)
    roll = skill_check(data["stats"].get(stat_key, 5),
                       data["skills"].get(skill, 2), dv, mods)

    out = {"npc": npc["name"], "success": roll["success"],
           "total": roll["total"], "dv": dv, "damage": 0, "net_damage": 0}

    if roll["success"]:
        w = WEAPONS.get(data.get("weapon", "heavy_pistol"), {"damage": "2d6"})
        dmg, faces = roll_dice(w.get("damage", "2d6"))
        sp = ARMOR.get(actor.get("armor", "leathers"), {}).get("sp", 0)
        net = max(0, dmg - sp)
        out.update({"damage": dmg, "armor_sp": sp, "net_damage": net})
        if net > 0:
            apply_damage(actor, net)
            out["actor_hp"] = actor["hp"]
            out["actor_wound"] = actor.get("wound")
    return out 