# scripts/09_fix_mojibake.py
import json
from pathlib import Path


def fix(s):
    try:
        return s.encode("cp1252").decode("utf-8")
    except Exception:
        return (s.replace("â–¶", "▶").replace("â—€", "◀")
                 .replace("â€”", "—").replace("â€œ", "“").replace("â€", "’"))


for p in [Path("data/extracted/blocks.jsonl"),
          Path("data/chunks/chunks.jsonl"),
          Path("index/meta.jsonl")]:
    if not p.exists():
        continue
    rows = [json.loads(l) for l in open(p, encoding="utf-8")]
    for r in rows:
        r["text"] = fix(r.get("text", ""))
        if "crumb" in r:
            r["crumb"] = fix(r["crumb"])
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("patched", p)