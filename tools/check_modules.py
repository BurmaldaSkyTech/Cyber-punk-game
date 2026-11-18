"""Проверяет не только синтаксис, но и наличие обязательных символов модуля."""
import importlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

CONTRACTS = {
    "backend.creation_catalog": ["ROLES", "ROLE_TEMPLATES", "DEFAULT_TEMPLATE",
                                 "HOUSE_STARTING_EB", "HOUSE_GEAR", "HOUSE_CYBER",
                                 "HOUSE_DRUGS", "HOUSE_PROGRAMS", "MARTIAL_FORMS",
                                 "template", "skill_master", "starting_eb",
                                 "catalog", "martial_options", "roll_stats"],
    "backend.creation": ["METHODS", "normalize_role", "methods", "limits",
                         "roll_stats", "options", "build", "random_character"],
    "backend.rules": ["get", "get_optional", "value_or", "verified", "put",
                      "put_many", "skeleton", "provenance", "status"],
    "backend.rules_tables": ["dv_table", "armor_table", "weapon_table", "max_hp"],
    "backend.combat_rules": ["aimed_penalty", "aimed_multiplier", "ablation_step",
                             "crit_trigger", "crit_bonus", "wound_state",
                             "wound_penalty", "death_save", "range_dv",
                             "dodge_dv", "melee_defense"],
    "backend.engine": ["DV", "ARMOR", "WEAPONS", "SKILL_STAT", "resolve_check",
                       "resolve_npc_reaction", "armor_sp", "ablate_armor",
                       "roll_initiative", "refresh_rules_tables"],
}

bad = 0
for mod_name, symbols in CONTRACTS.items():
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        print(f"FAIL import {mod_name}: {e}")
        bad += 1
        continue
    missing = [s for s in symbols if not hasattr(mod, s)]
    if missing:
        print(f"FAIL {mod_name}: нет {', '.join(missing)}")
        bad += len(missing)
    else:
        print(f"OK   {mod_name}: {len(symbols)} символов")
print(f"итого проблем: {bad}")
sys.exit(1 if bad else 0)