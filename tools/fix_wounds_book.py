"""Книжные ранения поверх wounds.py + чинит MU в нетраннинге."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]

WB = '''"""Книжные ранения: пороги/штрафы, крит по кубикам, спасброски с накоплением.
Формат результата совместим с wounds.apply_damage."""
import random

from backend import combat_rules, rules
from backend import wounds as base


def get_wound_state(hp, max_hp):
    return combat_rules.wound_state(hp, max_hp)


def get_wound_penalty(state, stat_key=None):
    return combat_rules.wound_penalty(state, stat_key)


def _book_table(location):
    key = "critical_injury_table_head" if location == "head" else "critical_injury_table_body"
    t = rules.get_optional("combat", key)
    return t if isinstance(t, dict) and t else None


def roll_critical_injury(location="auto", damage_type="bullet", rng=None):
    rng = rng or random
    roll = rng.randint(1, 6) + rng.randint(1, 6)
    table = _book_table(location)
    if table and table.get(str(roll)):
        return {"roll": roll, "location": location, "name": table[str(roll)], "source": "book"}
    house = base.roll_critical_injury(damage_type, rng=rng)
    return {"roll": roll, "location": location, "name": house, "source": "house",
            "note": "в книжной таблице извлечены только броски 2-6"}


def apply_damage(target, damage, weapon_key=None, crit=False, location="auto"):
    max_hp = int(target.get("max_hp") or 10)
    new_hp = int(target.get("hp", max_hp)) - int(damage)
    state = get_wound_state(new_hp, max_hp)
    info = None
    injury = None
    if crit:
        dtype = base.determine_damage_type(weapon_key) if weapon_key else "bullet"
        info = roll_critical_injury(location, dtype)
        injury = info["name"]
    return {
        "hp": new_hp,
        "wound_state": state,
        "penalty": get_wound_penalty(state),
        "move_penalty": get_wound_penalty(state, "MOVE"),
        "critical_injury": injury,
        "critical_injury_info": info,
        "death_save": state == "mortally",
        "dead": False,
    }


def death_save(target, rng=None):
    res = combat_rules.death_save(target)
    res["result"] = (f"d10={res['roll']} +{res['penalty']} против BODY {res['body']}: "
                     + ("смерть" if res["dead"] else "стабилизация"))
    return res


def stabilize(target, medic_skill, rng=None):
    return base.stabilize(target, medic_skill, rng=rng)
'''

(ROOT / "backend" / "wounds_book.py").write_text(WB, encoding="utf-8")
print("backend/wounds_book.py создан")

REBIND = '''
# --- книжные ранения перекрывают домашние (см. wounds_book) ---
from backend import wounds_book as _wb
from backend import wounds as _wounds_mod

apply_damage = _wb.apply_damage
get_wound_state = _wb.get_wound_state
get_wound_penalty = _wb.get_wound_penalty
death_save = _wb.death_save
_wounds_mod.apply_damage = _wb.apply_damage
_wounds_mod.get_wound_state = _wb.get_wound_state
_wounds_mod.get_wound_penalty = _wb.get_wound_penalty
_wounds_mod.death_save = _wb.death_save
'''

ep = ROOT / "backend" / "engine.py"
s = ep.read_text(encoding="utf-8")
report = []

if "from backend import wounds_book as _wb" not in s:
    anchor = "from . import netrunning"
    if anchor in s:
        s = s.replace(anchor, anchor + "\n" + REBIND, 1)
        report.append(("rebind wounds_book", 1))
    else:
        report.append(("rebind wounds_book", 0))

old = "apply_damage(target, total_damage, weapon_key=wkey, crit=crit)"
new = "apply_damage(target, total_damage, weapon_key=wkey, crit=crit, location=location)"
n = s.count(old)
if n:
    s = s.replace(old, new)
report.append(("player crit location", n))

old_npc = "            dr = apply_damage(target_player, net, weapon_key=wkey)"
new_npc = ("            _npc_crit = sum(1 for f in _faces if f == 6) >= combat_rules.crit_trigger()\n"
           "            _bonus = combat_rules.crit_bonus() if _npc_crit else 0\n"
           '            res["critical_success"] = _npc_crit\n'
           '            res["bonus_damage"] = _bonus\n'
           "            dr = apply_damage(target_player, net + _bonus, weapon_key=wkey, crit=_npc_crit)")
n = s.count(old_npc)
if n:
    s = s.replace(old_npc, new_npc)
report.append(("npc crit gating", n))

ep.write_text(s, encoding="utf-8")

np = ROOT / "backend" / "netrunning.py"
ns = np.read_text(encoding="utf-8")
if "def _mu_cost(" not in ns:
    ns = ns.rstrip() + '''


def _mu_cost(prog):
    raw = str((prog or {}).get("cost", "0"))
    digits = "".join(ch for ch in raw if ch.isdigit())
    return int(digits) if digits else 0


def calculate_net_stats(character):
    """Исправлено: MU считаются числами, а не строками."""
    int_stat = (character.get("stats") or {}).get("INT", 5)
    deck = get_cyberdeck(character.get("cyberdeck", "basic_deck")) or {"speed": 1, "slots": 4}
    progs = [get_program(p) for p in character.get("programs", [])]
    return {"speed": int_stat + int(deck.get("speed", 1)),
            "mu_total": int(deck.get("slots", 4)),
            "mu_used": sum(_mu_cost(p) for p in progs if p)}
'''
    np.write_text(ns, encoding="utf-8")
    report.append(("netrunning MU fix", 1))

print("=== PATCH REPORT ===")
for name, n in report:
    print(f"  {'OK ' if n else 'MISS'} {name}: {n}")