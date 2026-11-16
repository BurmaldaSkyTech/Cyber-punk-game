"""Принимает JSON от внешнего экстрактора (Grok), валидирует provenance,
пишет в data/rules. По умолчанию — как НЕподтверждённое (ожидает глаз человека).
Флаг --accept подтверждает только записи, прошедшие все проверки.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from backend import engine, rules

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAX_QUOTE = 240


def _norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def value_in_quote(value, quote):
    q = _norm(quote)
    if isinstance(value, (int, float)):
        return str(value) in q
    if isinstance(value, str):
        return _norm(value) in q
    if isinstance(value, dict):
        flat = []
        for v in value.values():
            flat.extend(v.values() if isinstance(v, dict) else [v])
        return any(_norm(x) in q for x in flat if x is not None)
    if isinstance(value, list):
        return any(_norm(x) in q for x in value)
    return False


def validate(e):
    problems = []
    if not e.get("pack") or not e.get("key"):
        problems.append("нет pack/key")
    page = e.get("page")
    if not isinstance(page, int) or page <= 0:
        problems.append("нет корректного page")
    quote = e.get("quote") or ""
    if not quote.strip():
        problems.append("нет quote")
    if len(quote) > MAX_QUOTE:
        problems.append(f"quote длиннее {MAX_QUOTE}")
    if e.get("value") is None:
        problems.append("value = null")
    elif quote and not value_in_quote(e["value"], quote):
        problems.append("значение не встречается в цитате")
    if e.get("confidence") == "low":
        problems.append("confidence=low")
    return problems


def diff_tables():
    print("\n=== РАСХОЖДЕНИЯ КОД vs КНИГА ===")
    rows = 0
    for pack, key, table, fields in [
        ("combat", "dv_table", engine.DV, None),
        ("armor", "table", engine.ARMOR, ["sp", "penalty", "price"]),
        ("weapons", "table", engine.WEAPONS, ["damage", "rof", "mag", "price", "skill"]),
    ]:
        book = rules.get(pack, key, house=None) if rules.entry(pack, key) else None
        if not isinstance(book, dict):
            print(f"[нет данных] {pack}.{key}")
            continue
        for k, v in table.items():
            if k not in book:
                print(f"[нет в книге] {pack}.{key}.{k}")
                rows += 1
                continue
            if fields and isinstance(v, dict):
                for f in fields:
                    if f in v and f in book[k] and v[f] != book[k][f]:
                        print(f"[MISMATCH] {pack}.{key}.{k}.{f}: код={v[f]} книга={book[k][f]}")
                        rows += 1
    print(f"итого расхождений: {rows}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    accept = "--accept" in sys.argv
    if not args:
        print("usage: python tools/rules_import.py <file.json> [--accept]")
        sys.exit(2)
    payload = json.loads(pathlib.Path(args[0]).read_text(encoding="utf-8"))
    ok, flagged = 0, 0
    for e in payload.get("entries", []):
        problems = validate(e)
        tag = "OK" if not problems else "FLAG"
        if problems:
            flagged += 1
        else:
            ok += 1
        verified = accept and not problems
        rules.put(e["pack"], e["key"], e.get("value"),
                  page=e.get("page"), chunk=e.get("chunk"),
                  note=f"grok:{e.get('confidence','?')}"
                       + (f" | {'; '.join(problems)}" if problems else ""),
                  verified=verified)
        print(f"[{tag}] {e['pack']}.{e['key']} page={e.get('page')} "
              f"verified={verified}" + (f" :: {'; '.join(problems)}" if problems else ""))
    for nf in payload.get("not_found", []):
        print(f"[NOT_FOUND] {nf.get('pack')}.{nf.get('key')}: {nf.get('reason')}")
    for d in payload.get("code_discrepancies", []):
        if d.get("verdict") == "mismatch":
            print(f"[CODE MISMATCH] {d.get('symbol')}: код={d.get('code')} "
                  f"книга={d.get('book')} стр.{d.get('page')}")
    print(f"\nпринято чисто: {ok}, с замечаниями: {flagged}, режим accept={accept}")
    diff_tables()