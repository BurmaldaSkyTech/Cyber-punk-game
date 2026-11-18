"""Переводит engine на combat_rules построчно: ни один несработавший якорь
не отменяет остальные правки. В конце печатает отчёт."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
ep = ROOT / "backend" / "engine.py"
s = ep.read_text(encoding="utf-8")
report = []


def sub(pattern, repl, name, flags=re.M):
    global s
    s2, n = re.subn(pattern, repl, s, flags=flags)
    report.append((name, n))
    if n:
        s = s2


if "from backend import combat_rules" not in s:
    if "from backend import rules" in s:
        s = s.replace("from backend import rules", "from backend import combat_rules, rules", 1)
    else:
        s = "from backend import combat_rules\n" + s
    report.append(("import combat_rules", 1))

sub(r"wound_state = get_wound_state\([\s\S]*?\)\n",
    'wound_state = combat_rules.wound_state(actor.get("hp", actor.get("max_hp", 10)),\n'
    '                                          actor.get("max_hp", 10))\n',
    "wound_state")

sub(r'^\s*wound_pen = rules\.get_optional\("combat", "wound_penalties"\)\n', "", "wound_pen var")
sub(r'^\s*mods = wound_pen\.get\(wound_state, 0\).*$',
    "    mods = combat_rules.wound_penalty(wound_state, stat_key)", "mods (dict variant)")
sub(r'^\s*mods = get_wound_penalty\(wound_state\)$',
    "    mods = combat_rules.wound_penalty(wound_state, stat_key)", "mods (legacy)")
sub(r'"wound_penalty": wound_pen if isinstance\(wound_pen, dict\) else mods,',
    '"wound_penalty": mods,', "wound_penalty field")

sub(r'^\s*penalties = _crule\("aimed_shot_penalties"\).*\n', "", "aimed penalties var")
sub(r'^(\s*)aimed_pen = int\(penalties\.get\(location, 0\)\)',
    r"\1aimed_pen = combat_rules.aimed_penalty(location)", "aimed penalty")

sub(r'^\s*mults = _crule\("aimed_shot_multipliers"\).*\n', "", "mults var")
sub(r'^(\s*)mult = float\(mults\.get\(location, 1\)\)',
    r"\1mult = combat_rules.aimed_multiplier(location)", "multiplier")
sub(r'^(\s*)raw = int\(round\(dmg \* mult\)\)', r"\1raw = dmg", "raw damage")
sub(r'^(\s*)net = max\(0, raw - sp\)$', r"\1net = max(0, raw - sp) * mult", "net after armor")

sub(r'crit = sixes >= int\(_crule\("critical_injury_trigger"\) or 2\)',
    "crit = sixes >= combat_rules.crit_trigger()", "crit trigger")
sub(r'bonus = int\(_crule\("critical_injury_bonus"\) or 0\) if crit else 0',
    "bonus = combat_rules.crit_bonus() if crit else 0", "crit bonus")
sub(r'step = int\(_crule\("armor_ablation"\) or 0\)',
    "step = combat_rules.ablation_step()", "ablation step")
sub(r'death_result = death_save\(target\)',
    "death_result = combat_rules.death_save(target)", "death save")

sub(r'^(\s*)dv = 13$',
    r"\1dv = combat_rules.range_dv(wkey, 3) or 13\n"
    r"\1dodge = combat_rules.dodge_dv(target_player)\n"
    r"\1if dodge is not None:\n"
    r"\1    dv = max(dv, dodge)", "npc dv")
sub(r'^(\s*)sp = ARMOR\.get\(target_player\.get\("armor", "leathers"\), \{\}\)\.get\("sp", 0\)$',
    r"\1sp = armor_sp(target_player)\n"
    r"\1abl = ablate_armor(target_player, dmg > sp)\n"
    r"\1if abl:\n"
    r'\1    res["armor_ablation"] = abl', "npc armor sp")

anchor = "    mech = skill_check(stat, sk_lvl, dv, mods)\n"
if anchor in s and "combat_rules.melee_defense" not in s:
    inject = ('    if at == "attack_melee" and target is not None:\n'
              '        dv = combat_rules.melee_defense(target)\n'
              '    elif at == "attack_ranged":\n'
              '        rdv = combat_rules.range_dv(judge.get("weapon") or "heavy_pistol", 3)\n'
              '        if rdv:\n'
              '            dv = rdv\n'
              '        dodge = combat_rules.dodge_dv(target) if target is not None else None\n'
              '        if dodge is not None:\n'
              '            dv = max(dv, dodge)\n')
    s = s.replace(anchor, inject + anchor, 1)
    report.append(("player attack DV", 1))

ep.write_text(s, encoding="utf-8")
print("=== ENGINE PATCH REPORT ===")
for name, n in report:
    print(f"  {'OK ' if n else 'MISS'} {name}: {n}")