# scripts/17_rate_last.py
"""
Оценивает последний ход последней сессии.
Запуск: python scripts\17_rate_last.py <rating> [edited_narration]
"""
import sys, psycopg

DSN = "postgresql://postgres:412321@localhost:7777/cpr"

def main():
    if len(sys.argv) < 2:
        print("Usage: python 17_rate_last.py <rating 1-5> [edited_narration]")
        return

    rating = int(sys.argv[1])
    edited = sys.argv[2] if len(sys.argv) > 2 else None

    conn = psycopg.connect(DSN)
    cur = conn.cursor()

    # Берём последний ход из последней сессии
    cur.execute("""
        SELECT id, session_id, turn_no, narration
        FROM turns
        ORDER BY created_at DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if not row:
        print("Нет ходов в таблице.")
        return

    tid, sid, turn_no, narration = row
    print(f"Последний ход: сессия={sid}, ход={turn_no}")
    print(f"Нарратив: {narration[:200]}...")
    print(f"Оценка: {rating}/5")
    if edited:
        print(f"Правка: {edited[:200]}...")

    cur.execute("""
        UPDATE turns
        SET rating=%s, edited_narration=COALESCE(%s, edited_narration)
        WHERE id=%s
    """, (rating, edited, tid))
    conn.commit()
    print(f"Сохранено (turn_id={tid})")


if __name__ == "__main__":
    main()