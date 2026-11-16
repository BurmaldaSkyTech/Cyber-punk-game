"""Сверяет хардкод в engine/creation с подтверждёнными значениями из книги.
Неподтверждённые ключи — это строка отчёта, а не исключение.
Код выхода 1, если есть расхождения или неподтверждённые ключи."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from backend import creation, engine, rules

problems = []


def check_table(pack, key, code_table, fields=None):
    book = rules.get_optional(pack, key)
    if not isinstance(book, dict):
        problems.append(f"[UNVERIFIED] {pack}.{key}: в коде {len(code_table)} записей, книга не подтверждена")
        return
    for k, v in code_table.items():
        if k not in book:
            problems.append(f"[MISSING_IN_BOOK] {pack}.{key}.{k}")
            continue
        if fields and isinstance(v, dict) and isinstance(book[k], dict):
            for f in fields:
                if f in v and f in book[k] and v[f] != book[k][f]:
                    problems.append(f"[MISMATCH] {pack}.{key}.{k}.{f}: код={v[f]} книга={book[k][f]}")


if __name__ == "__main__":
    check_table("combat", "dv_table", engine.DV)
    check_table("armor", "table", engine.ARMOR, ["sp", "penalty", "price"])
    check_table("weapons", "table", engine.WEAPONS, ["damage", "rof", "mag", "price", "skill"])

    lim = creation.limits()
    for key, val in [("stat_pool_edgerunner", lim["stat_pool"]),
                     ("skill_pool_edgerunner", lim["skill_pool"]),
                     ("skill_max_at_creation", lim["skill_max"])]:
        if not rules.provenance("creation", key)["verified"]:
            problems.append(f"[HOUSE] creation.{key}={val} (домашнее, книга не подтверждена)")

    print("=== RULES AUDIT ===")
    for p in problems:
        print(p)
    print(f"итого проблем: {len(problems)}")
    hits = rules.house_hits()
    print(f"house-hits: {len(hits)}")
    for k in sorted(hits):
        print(f"  {k}")
    sys.exit(1 if problems else 0)