"""Прицел после брони, книжные раны/спасброски, DV по дистанции и уклонение,
снятие выдуманного алиаса bodyplate."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]

# --- rules_tables: убрать алиас bodyplate ---
rp = ROOT / "backend" / "rules_tables.py"
r = rp.read_text(encoding="utf-8")
old_alias = '''        if "metalgear" in out and "bodyplate" in out:
            out["bodyplate"].update(out["metalgear"])
            out["bodyplate"]["book_alias"] = "metalgear"
'''
new_alias = '''        if "bodyplate" in out:
            out["bodyplate"]["house_item"] = True
            out["bodyplate"]["note"] = "нет в книге (стр.185); домашний предмет"
'''
if old_alias in r:
    r = r.replace(old_alias, new_alias)
    rp.write_text(r, encoding="utf-8")
    print("rules_tables: bodyplate alias снят")

# --- engine ---
ep = ROOT / "backend" / "engine.py"
s = ep.read_text(encoding="utf-8")
if "from backend import combat_rules" not in s:
    s = s.replace("from backend import rules", "from backend import combat_rules, rules", 1)

s2, n = re.subn(r"wound_state = get_wound_state\([\s\S]*?\)\n",
                'wound_state = combat_rules.wound_state(actor.get("hp", actor.get("max_hp", 10)),\n'
                '                                          actor.get("max_hp", 10))\n', s, count=1)
assert n == 1, "wound_state anchor"
s = s2

old_mods = "    mods = wound_pen.get(wound_state, 0) if isinstance(wound_pen, dict) else get_wound_penalty(wound_state)\n"
assert old_mods in s, "mods anchor"
s = s.replace(old_mods, "    mods = combat_rules.wound_penalty(wound_state, stat_key)\n")

old_aim = '''        penalties = _crule("aimed_shot_penalties") or {}
        aimed_pen = int(penalties.get(location, 0))
'''
assert old_aim in s, "aimed anchor"
s = s.replace(old_aim, "        aimed_pen = combat_rules.aimed_penalty(location)\n")

old_dmg = '''        mults = _crule("aimed_shot_multipliers") or {}
        mult = float(mults.get(location, 1))
        raw = int(round(dmg * mult))
        sp = armor_sp(target) if target else 0
        net = max(0, raw - sp)
'''
new_dmg = '''        mult = combat_rules.aimed_multiplier(location)
        raw = dmg
        sp = armor_sp(target) if target else 0
        net = max(0, raw - sp) * mult
'''
assert old_dmg in s, "damage anchor"
s = s.replace(old_dmg, new_dmg)

s = s.replace('crit = sixes >= int(_crule("critical_injury_trigger") or 2)',
              'crit = sixes >= combat_rules.crit_trigger()')
s = s.replace('bonus = int(_crule("critical_injury_bonus") or 0) if crit else 0',
              'bonus = combat_rules.crit_bonus() if crit else 0')
s = s.replace("death_result = death_save(target)", "death_result = combat_rules.death_save(target)")

old_npc = '''    roll, _ = roll_dice("1d10")
    total = roll + stat + skill
    dv = 13
'''
new_npc = '''    roll, _ = roll_dice("1d10")
    total = roll + stat + skill
    dv = combat_rules.range_dv(wkey, 3) or 13
    dodge = combat_rules.dodge_dv(target_player)
    if dodge is not None:
        dv = max(dv, dodge)
'''
assert old_npc in s, "npc dv anchor"
s = s.replace(old_npc, new_npc)

old_npc_sp = '        sp = ARMOR.get(target_player.get("armor", "leathers"), {}).get("sp", 0)\n'
if old_npc_sp in s:
    s = s.replace(old_npc_sp,
                  '        sp = armor_sp(target_player)\n'
                  '        abl = ablate_armor(target_player, dmg > sp)\n'
                  '        if abl:\n'
                  '            res["armor_ablation"] = abl\n')

ep.write_text(s, encoding="utf-8")
print("engine: книжные раны, прицел после брони, death save, DV по дистанции, уклонение")