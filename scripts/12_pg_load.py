# scripts/12_pg_load.py
import json, os
from pathlib import Path
import psycopg

ROOT = Path(__file__).resolve().parent.parent
DSN = os.environ.get("PG_DSN", "postgresql://postgres:postgres@localhost:5432/cpr")

conn = psycopg.connect(DSN, connect_timeout=5)
cur = conn.cursor()

n = 0
for p in sorted((ROOT / "data" / "normalized").glob("*.jsonl")):
    family = p.stem
    cur.execute("DELETE FROM game_data WHERE family=%s", (family,))
    for line in open(p, encoding="utf-8"):
        rec = json.loads(line)
        key = rec.pop("key")
        page = rec.pop("_page", None)
        val = rec.pop("_validated", False)
        cur.execute("""
            INSERT INTO game_data (family, key, data, source_page, validated)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (family, key) DO UPDATE
              SET data = EXCLUDED.data, source_page = EXCLUDED.source_page,
                  validated = EXCLUDED.validated
        """, (family, key, json.dumps(rec, ensure_ascii=False), page, val))
        n += 1
print("game_data rows:", n)

m = 0
for line in open(ROOT / "data" / "chunks" / "chunks.jsonl", encoding="utf-8"):
    c = json.loads(line)
    cur.execute("""
        INSERT INTO lore_chunks (id, crumb, page_start, page_end, kind, text)
        VALUES (%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO UPDATE SET text = EXCLUDED.text
    """, (c["id"], c["crumb"], c["page_start"], c["page_end"], c["kind"], c["text"]))
    m += 1
print("lore_chunks rows:", m)

conn.commit()
cur.execute("SELECT family, count(*) FROM game_data GROUP BY family ORDER BY 2 DESC")
for row in cur.fetchall():
    print(row)