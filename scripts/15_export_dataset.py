# scripts/15_export_dataset.py
import json, os
from pathlib import Path
import psycopg

ROOT = Path(__file__).resolve().parent.parent
DSN = os.environ.get("PG_DSN", "postgresql://postgres:412321@localhost:7777/cpr")
OUT = ROOT / "data" / "dataset"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    conn = psycopg.connect(DSN)
    cur = conn.cursor()

    # Экспорт ходов с rating >= 4 или с edited_narration
    cur.execute("""
        SELECT session_id, turn_no, player, action_text, judge, mechanics, narration,
               edited_narration, rating
        FROM turns
        WHERE rating >= 4 OR edited_narration IS NOT NULL
        ORDER BY session_id, turn_no
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} high-quality turns")

    dataset = []
    for row in rows:
        sid, turn_no, player, action_text, judge, mechanics, narration, edited, rating = row

        # Используем edited_narration если есть, иначе narration
        final_narration = edited if edited else narration

        # Формируем input для модели
        mech_str = json.dumps(mechanics, ensure_ascii=False)
        input_text = (
            f"Персонаж: {player}\n"
            f"Действие: {action_text}\n"
            f"Факты броска: {mech_str}\n"
            f"Результат: {'УСПЕХ' if mechanics.get('success') else 'ПРОВАЛ'}"
        )

        # Формат Alpaca для QLoRA
        dataset.append({
            "instruction": "Напиши короткий нарратив для хода в киберпанк-настолке.",
            "input": input_text,
            "output": final_narration
        })

    # Сохраняем в JSONL
    out_path = OUT / "dataset.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Exported {len(dataset)} examples to {out_path}")
    print(f"\nStatistics:")
    print(f"  rating >= 4: {sum(1 for r in rows if r[8] and r[8] >= 4)}")
    print(f"  edited: {sum(1 for r in rows if r[7])}")

    conn.close()


if __name__ == "__main__":
    main()