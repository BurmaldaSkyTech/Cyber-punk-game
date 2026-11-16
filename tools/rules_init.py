"""Скелеты пакетов правил: значения пустые, заполняются только из книги."""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from backend import rules

PACKS = {
    "creation": [
        "methods", "roles", "stat_list", "stat_min", "stat_max",
        "stat_pool_edgerunner", "skill_pool_edgerunner", "skill_max_at_creation",
        "skill_list", "hp_formula", "humanity_formula", "starting_eb",
        "gear_budget", "role_abilities",
    ],
    "combat": [
        "dv_table", "range_dv", "aimed_shot_penalties", "aimed_shot_multipliers",
        "armor_ablation", "critical_injury_trigger", "critical_injury_bonus",
        "critical_injury_table", "wound_states", "wound_penalties",
        "death_save_formula", "initiative_formula", "autofire_rules",
        "rof_rules", "melee_opposed_by", "ranged_defense",
    ],
    "armor": ["table"],
    "weapons": ["table"],
    "cyberware": ["table", "humanity_loss_rules"],
    "netrunning": ["architectures", "program_list", "interface_dv", "black_ice"],
    "gear": ["table", "services"],
}

if __name__ == "__main__":
    t0 = time.time()
    total = 0
    for pack, keys in PACKS.items():
        added = rules.skeleton(pack, keys)
        total += len(added)
        print(f"{pack}: +{len(added)} новых из {len(keys)}")
    print(f"готово за {time.time() - t0:.2f} c, добавлено ключей: {total}")