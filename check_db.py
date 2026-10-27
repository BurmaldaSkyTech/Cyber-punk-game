# check_db.py
import psycopg
import json
import traceback

DSN = "postgresql://postgres:412321@localhost:7777/cpr"

try:
    print("Подключаюсь к БД...")
    conn = psycopg.connect(DSN)
    cur = conn.cursor()

    print("\n=== Все таблицы в game_data ===")
    cur.execute("SELECT family, count(*) FROM game_data GROUP BY family ORDER BY 2 DESC")
    for row in cur.fetchall():
        print(f"  {row[0]:25s} {row[1]}")

    print("\n=== Броня (armor) ===")
    cur.execute("SELECT data FROM game_data WHERE family='armor'")
    rows = cur.fetchall()
    print(f"Найдено строк: {len(rows)}")
    if rows:
        print("\nПервые 3 записи:")
        for i, row in enumerate(rows[:3]):
            print(f"{i+1}. {json.dumps(row[0], indent=2, ensure_ascii=False)}")

    print("\n=== Оружие (weapons) ===")
    cur.execute("SELECT data FROM game_data WHERE family='weapons' LIMIT 3")
    rows = cur.fetchall()
    print(f"Найдено строк (показано 3): {len(rows)}")
    if rows:
        for i, row in enumerate(rows):
            print(f"{i+1}. {json.dumps(row[0], indent=2, ensure_ascii=False)}")

    conn.close()
    print("\nГотово.")

except Exception as e:
    print(f"\nОШИБКА: {e}")
    traceback.print_exc()

print("\nНажмите Enter для выхода...")
input()