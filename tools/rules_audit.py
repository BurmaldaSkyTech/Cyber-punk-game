"""Сверяет код с книгой через те же отображения, что и rules_tables.
Ложных срабатываний на структуру penalty и категории ближнего боя нет."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from backend import creation, engine, rules
from tools.rules_normalize import MELEE_MAP

ARMOR_ALIASES = {"bodyplate": "metalgear"}
problems = []


def check_dv():
    book = rules.get_optional("combat", "dv_table")
    if not isinstance(book, dict):
        problems.append("[UNVERIFIED] combat.dv_table")
        return
    for k, v in engine.DV.items():
        if k in book and int(book[k]) != int(v):
            problems.append(f"[MISMATCH] dv.{k}: код={v} книга={book[k]}")


def check_armor():
    book = rules.get_optional("armor", "table")
    if not isinstance(book, dict):
        problems.append("[UNVERIFIED] armor.table")
        return
    for k, v in engine.ARMOR.items():
        bk = ARMOR_ALIASES.get(k, k)
        if bk not in book:
            problems.append(f"[NEEDS_EXTRACT] armor.{k}")
            continue
        b = book[bk]
        if "sp" in b and v.get("sp") != b["sp"]:
            problems.append(f"[MISMATCH] armor.{k}.sp: код={v.get('sp')} книга={b['sp']}")
        pen = b.get("penalty")
        bv = pen.get("value", 0) if isinstance(pen, dict) else (pen or 0)
        if int(v.get("penalty", 0) or 0) != int(bv):
            problems.append(f"[MISMATCH] armor.{k}.penalty: код={v.get('penalty')} книга={bv}")
        if b.get("price") is not None and v.get("price") != b["price"]:
            problems.append(f"[MISMATCH] armor.{k}.price: код={v.get('price')} книга={b['price']}")


def check_weapons():
    book = rules.get_optional("weapons", "table")
    if not isinstance(book, dict):
        problems.append("[UNVERIFIED] weapons.table")
        return
    for k, v in engine.WEAPONS.items():
        bk = MELEE_MAP.get(k, k)
        if bk not in book:
            problems.append(f"[NEEDS_EXTRACT] weapons.{k}")
            continue
        b = book[bk]
        for f in ("damage", "rof", "mag", "skill"):
            if f in b and f in v and v[f] != b[f]:
                problems.append(f"[MISMATCH] weapons.{k}.{f}: код={v[f]} книга={b[f]}")


if __name__ == "__main__":
    check_dv()
    check_armor()
    check_weapons()
    lim = creation.limits()
    for key, val in [("stat_pool_edgerunner", lim["stat_pool"]),
                     ("skill_pool_edgerunner", lim["skill_pool"]),
                     ("skill_max_at_creation", lim["skill_max"]),
                     ("hp_formula", None)]:
        if not rules.provenance("creation", key)["verified"]:
            problems.append(f"[HOUSE] creation.{key}" + (f"={val}" if val is not None else ""))
    print("=== RULES AUDIT ===")
    for p in problems:
        print(p)
    print(f"итого проблем: {len(problems)}")
    sys.exit(1 if problems else 0)