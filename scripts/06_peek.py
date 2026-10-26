# scripts/06_peek.py
import json, sys, random

path = "data/chunks/chunks.jsonl"
chunks = [json.loads(l) for l in open(path, encoding="utf-8")]
print("total chunks:", len(chunks))

idx = [int(x) for x in sys.argv[1:]] or random.sample(range(len(chunks)), 6)
for i in idx:
    c = chunks[i]
    print("=" * 72)
    print(f"#{i}  kind={c['kind']}  pages={c['page_start']}-{c['page_end']}")
    print("CRUMB:", c["crumb"])
    print(c["text"][:450].replace("\n", " | "))