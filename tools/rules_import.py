"""Приёмка JSON внешнего экстрактора: нормализация, валидация provenance,
детект внутренних конфликтов. По умолчанию пишет как НЕподтверждённое."""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from backend import rules
from tools.rules_normalize import normalize_entry

MAX_QUOTE = 240
NUMERIC_KEYS = {"stat_min", "stat_max", "stat_pool_edgerunner",
                "skill_pool_edgerunner", "skill_max_at_creation", "starting_eb"}


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


def conflicts_for(payload, pack, key):
    """Ищем в code_discrepancies утверждения о том же параметре с другим значением."""
    out = []
    tail = key.replace("_edgerunner", "")
    for d in payload.get("code_discrepancies", []):
        sym = (d.get("symbol") or "").lower()
        if tail and tail in sym and d.get("book") is not None:
            out.append(d)
    return out


def validate(e, payload):
    problems = []
    pack, key = e.get("pack"), e.get("key")
    if not pack or not key:
        problems.append("нет pack/key")
    page = e.get("page")
    if not isinstance(page, int) or page <= 0:
        problems.append("нет корректного page")
    quote = e.get("quote") or ""
    if not quote.strip():
        problems.append("нет quote")
    if len(quote) > MAX_QUOTE:
        problems.append(f"quote длиннее {MAX_QUOTE}")
    val = e.get("value")
    if val is None:
        problems.append("value = null")
    if key in NUMERIC_KEYS and not isinstance(val, (int, float)):
        problems.append(f"ожидалось число, получено {type(val).__name__}")
    if isinstance(val, (int, float, str)) and quote and not value_in_quote(val, quote):
        problems.append("значение не встречается в цитате")
    if e.get("confidence") == "low":
        problems.append("confidence=low")
    for d in conflicts_for(payload, pack, key):
        if d.get("book") != val:
            problems.append(f"КОНФЛИКТ с {d.get('symbol')}: book={d.get('book')}")
    return problems


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    accept = "--accept" in sys.argv
    if not args:
        print("usage: python -m tools.rules_import <file.json> [--accept]")
        sys.exit(2)
    payload = json.loads(pathlib.Path(args[0]).read_text(encoding="utf-8"))
    ok = flagged = 0
    for e in payload.get("entries", []):
        raw = e.get("value")
        norm = normalize_entry(e.get("pack"), e.get("key"), raw)
        problems = validate(dict(e, value=norm), payload)
        if problems:
            flagged += 1
        else:
            ok += 1
        verified = accept and not problems
        rules.put(e["pack"], e["key"], norm, page=e.get("page"), chunk=e.get("chunk"),
                  note=f"grok:{e.get('confidence','?')}"
                       + (f" | {'; '.join(problems)}" if problems else ""),
                  verified=verified)
        mark = "OK  " if not problems else "FLAG"
        print(f"[{mark}] {e['pack']}.{e['key']} p.{e.get('page')} verified={verified}"
              + (f"\n        {'; '.join(problems)}" if problems else ""))
    for nf in payload.get("not_found", []):
        print(f"[SKIP] {nf.get('pack')}.{nf.get('key')}: {nf.get('reason')}")
    print(f"\nчистых: {ok}, с замечаниями: {flagged}, accept={accept}")