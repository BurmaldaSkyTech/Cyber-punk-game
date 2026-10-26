# scripts/07_find.py
import json, sys

pat = sys.argv[1].lower()
for l in open("data/chunks/chunks.jsonl", encoding="utf-8"):
    c = json.loads(l)
    if pat in c["text"].lower():
        print(f"#{c['id']}  p{c['page_start']}-{c['page_end']}  {c['crumb'][:70]}")