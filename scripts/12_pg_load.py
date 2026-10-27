# scripts/12_pg_load.py
import json, os
from pathlib import Path
import psycopg

ROOT = Path(__file__).resolve().parent.parent

# Ваши настройки: порт 7777, пароль 412321
DSN_SERVER = os.environ.get("PG_DSN_SERVER", "postgresql://postgres:412321@localhost:7777/postgres")
DSN_CPR    = os.environ.get("PG_DSN",        "postgresql://postgres:412321@localhost:7777/cpr")

def ensure_database():
    print("Connecting to server to ensure database exists...")
    try:
        with psycopg.connect(DSN_SERVER, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname='cpr'")
                if not cur.fetchone():
                    cur.execute("CREATE DATABASE cpr")
                    print("Database 'cpr' created.")
                else:
                    print("Database 'cpr' already exists.")
    except Exception as e:
        print(f"Error connecting to server: {e}")
        raise

def main():
    ensure_database()

    print(f"Connecting to {DSN_CPR}...")
    conn = psycopg.connect(DSN_CPR)
    cur = conn.cursor()

    # 1. Применяем схему
    schema_path = ROOT / "schema.sql"
    if schema_path.exists():
        print("Applying schema...")
        cur.execute(schema_path.read_text(encoding="utf-8"))
        conn.commit()

    # 2. Загружаем данные (game_data)
    n = 0
    norm_dir = ROOT / "data" / "normalized"
    if norm_dir.exists():
        for p in sorted(norm_dir.glob("*.jsonl")):
            family = p.stem
            cur.execute("DELETE FROM game_data WHERE family=%s", (family,))
            for line in open(p, encoding="utf-8"):
                rec = json.loads(line)
                if "key" not in rec:  # <-- ДОБАВЬТЕ ЭТУ СТРОКУ
                    continue          # <-- И ЭТУ
                key = rec.pop("key")
                page = rec.pop("_page", None)
                val = rec.pop("_validated", False)
                # ... дальше без изменений
                cur.execute("""
                    INSERT INTO game_data (family, key, data, source_page, validated)
                    VALUES (%s,%s,%s,%s,%s)
                    ON CONFLICT (family, key) DO UPDATE
                      SET data = EXCLUDED.data, source_page = EXCLUDED.source_page,
                          validated = EXCLUDED.validated
                """, (family, key, json.dumps(rec, ensure_ascii=False), page, val))
                n += 1
    print(f"game_data rows loaded: {n}")

    # 3. Загружаем чанки (lore_chunks)
    m = 0
    chunks_path = ROOT / "data" / "chunks" / "chunks.jsonl"
    if chunks_path.exists():
        for line in open(chunks_path, encoding="utf-8"):
            c = json.loads(line)
            cur.execute("""
                INSERT INTO lore_chunks (id, crumb, page_start, page_end, kind, text)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET text = EXCLUDED.text
            """, (c["id"], c["crumb"], c["page_start"], c["page_end"], c["kind"], c["text"]))
            m += 1
    print(f"lore_chunks rows loaded: {m}")

    conn.commit()
    
    # 4. Отчет
    cur.execute("SELECT family, count(*) FROM game_data GROUP BY family ORDER BY 2 DESC")
    print("\nData in database:")
    for row in cur.fetchall():
        print(f"  {row[0]:25s} {row[1]}")
    
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()