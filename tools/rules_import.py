import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from backend import rules
from tools.rules_normalize import normalize_entry

NUMERIC = {"stat_min", "stat_max", "stat_pool_edgerunner", "skill_pool_edgerunner",
           "skill_max_at_creation", "starting_eb"}
FORMULA = {"hp_formula", "humanity_formula", "death_save_formula", "initiative_formula"}
SYN = {"emp": ("empathy",), "hum": ("humanity",), "body": ("body",),
       "will": ("will", "willpower"), "ref": ("reflex",), "dex": ("dexterity",)}


def norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def in_quote(v, q):
    q = norm(q)
    if isinstance(v, (int, float)):
        return str(v) in q
    if isinstance(v, str):
        return norm(v) in q
    if isinstance(v, dict):
        vals = []
        for x in v.values():
            vals.extend(x.values() if isinstance(x, dict) else [x])
        return any(norm(x) in q for x in vals if x is not None)
    if isinstance(v, list):
        return any(norm(x) in q for x in v)
    return False


def formula_ok(v, q):
    q = norm(q)
    nums = re.findall(r"\d+", str(v))
    if not nums or not all(n in q for n in nums):
        return False
    for i in re.findall(r"\b[A-Z]{2,}\b", str(v)):
        low = i.lower()
        if low in q or any(s in q for s in SYN.get(low, ())):
            continue
        return False
    return True


def conflicts(payload, key):
    tail = key.replace("_edgerunner", "")
    return [d for d in payload.get("code_discrepancies", [])
            if tail and tail in (d.get("symbol") or "").lower() and d.get("book") is not None]


def check(e, payload):
    p = []
    page, quote, val, key = e.get("page"), e.get("quote") or "", e.get("value"), e.get("key")
    if not isinstance(page, int) or page <= 0:
        p.append("нет page")
    if not quote.strip():
        p.append("нет quote")
    if len(quote) > 240:
        p.append("длинная quote")
    if val is None:
        p.append("value=null")
    if key in NUMERIC and not isinstance(val, (int, float)):
        p.append("ожидалось число")
    if quote and isinstance(val, (int, float, str)):
        ok = formula_ok(val, quote) if key in FORMULA else in_quote(val, quote)
        if not ok:
            p.append("цитата не подтверждает значение")
    if e.get("confidence") == "low":
        p.append("confidence=low")
    for d in conflicts(payload, key):
        if d.get("book") != val:
            p.append(f"КОНФЛИКТ {d.get('symbol')}={d.get('book')}")
    return p


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    accept = "--accept" in sys.argv
    if not args:
        print("usage: python -m tools.rules_import <file.json> [--accept]")
        return
    payload = json.loads(pathlib.Path(args[0]).read_text(encoding="utf-8"))
    ok = bad = 0
    for e in payload.get("entries", []):
        val = normalize_entry(e.get("pack"), e.get("key"), e.get("value"))
        probs = check(dict(e, value=val), payload)
        if probs:
            bad += 1
        else:
            ok += 1
        verified = accept and not probs
        note = f"grok:{e.get('confidence','?')}" + (f" | {'; '.join(probs)}" if probs else "")
        rules.put(e["pack"], e["key"], val, page=e.get("page"), chunk=e.get("chunk"),
                  note=note, verified=verified)
        print(f"[{'OK  ' if not probs else 'FLAG'}] {e['pack']}.{e['key']} p.{e.get('page')} verified={verified}")
        for x in probs:
            print(f"        {x}")
    print(f"чистых: {ok}, с замечаниями: {bad}, accept={accept}")


if __name__ == "__main__":
    main()