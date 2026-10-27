# check_tables_raw.py
import json
from pathlib import Path

TABLES = Path("data/extracted/tables.jsonl")

# Ищем страницы, где должны быть броня и оружие
targets = ["armor", "stopping power", "weapon", "damage", "ammo"]

for line in open(TABLES, encoding="utf-8"):
    t = json.loads(line)
    md = t.get("markdown", "")
    low = md.lower()
    if any(k in low for k in targets):
        if t["page"] in [342, 343, 344, 345, 346, 347, 351, 352, 353]:
            print(f"\n{'='*70}")
            print(f"PAGE {t['page']}")
            print(f"{'='*70}")
            print(md[:1500])
            print()