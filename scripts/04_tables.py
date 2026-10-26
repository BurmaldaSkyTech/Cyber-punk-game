# scripts/04_tables.py
import json, csv, re
from pathlib import Path

TABLES = Path("data/extracted/tables.jsonl")
OUT = Path("data/tables")
OUT.mkdir(parents=True, exist_ok=True)

tables = [json.loads(l) for l in open(TABLES, encoding="utf-8")]
print(f"tables found: {len(tables)}")

buckets = {}
for t in tables:
    rows = t.get("rows") or []
    if not rows:
        continue
    header = " ".join(str(c or "") for c in rows[0]).lower()
    key = re.sub(r"[^a-z ]+", "", header).strip()[:60] or "unknown"
    buckets.setdefault(key, []).append(t)

for key, items in sorted(buckets.items(), key=lambda x: -len(x[1])):
    safe = re.sub(r"[^a-z0-9]+", "_", key)[:50].strip("_") or "unknown"
    path = OUT / f"{safe}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for t in items:
            w.writerow([f"# PAGE {t['page']}"])
            for r in t["rows"]:
                w.writerow(["" if c is None else str(c).replace("\n", " ").strip() for c in r])
            w.writerow([])
    print(f"{len(items):3d} tables -> {path}")