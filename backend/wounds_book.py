"""Книжные ранения: пороги/штрафы, крит по кубикам, спасброски с накоплением.
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
