"""Снимок ядра бросков и ранений: то, что не попадало в общий SNAPSHOT."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools import snapshot

snapshot.TARGETS["backend/engine.py"] = [
    "DV", "ARMOR", "WEAPONS", "SKILL_STAT", "COMBAT_HOUSE",
    "roll_dice", "skill_check", "apply_damage",
    "get_wound_state", "get_wound_penalty", "death_save",
    "resolve_assist", "armor_sp", "ablate_armor", "roll_initiative",
    "refresh_rules_tables", "resolve_check", "_npc_attack_roll",
]
snapshot.TARGETS["backend/rules_tables.py"] = [
    "dv_table", "armor_table", "weapon_table", "max_hp",
]
snapshot.TARGETS["backend/creation.py"] = [
    "HOUSE", "limits", "options", "build", "_finalize",
]
snapshot.JS_TARGETS = {}

if __name__ == "__main__":
    text, stats = snapshot.dump()
    dest = snapshot.ROOT / "SNAPSHOT_CORE.md"
    dest.write_text(text, encoding="utf-8")
    print(f"SNAPSHOT_CORE.md: {len(text)} chars")
    for rel, got, total in stats:
        print(f"  {rel}: {got}/{total}")