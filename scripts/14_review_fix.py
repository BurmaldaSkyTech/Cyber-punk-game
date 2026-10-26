# scripts/14_review_fix.py
import json, os, sys, importlib.util, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / "data" / "normalized" / "review_queue.jsonl"
OUT = ROOT / "data" / "normalized"
MODEL = os.environ.get("FIX_MODEL", "qwen2.5-coder:32b")
OLLAMA = "http://localhost:11434/api/chat"

sys.path.insert(0, str(ROOT))
_spec = importlib.util.spec_from_file_location("norm", ROOT / "scripts" / "11_normalize_tables.py")
norm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(norm)

SYS = """Ты — реставратор таблиц книги Cyberpunk RED.
Получаешь: family, сырую markdown-таблицу, список подозрений.
Верни ИСПРАВЛЕННЫЕ строки в схеме этой family.
ПРАВИЛА:
1. Значения КОПИРУЙ дословно из ячеек сырой таблицы.
2. Если таблица свёрнута (сначала все имена, затем описания, затем цены) — разверни её.
3. Строки шапок и разделителей не переноси.
4. Не знаешь значение -> null. Ничего не выдумывай.
Верни ТОЛЬКО JSON: {"family": str, "rows": [ ... ]}"""


def call32b(entry):
    user = (f"family: {entry.get('family')}\n"
            f"problems: {json.dumps(entry.get('problems', []), ensure_ascii=False)}\n"
            f"note: {entry.get('note')}\n"
            f"RAW TABLE:\n{entry.get('raw', '')}")
    r = requests.post(OLLAMA, json={
        "model": MODEL, "stream": False, "format": "json",
        "messages": [{"role": "system", "content": SYS},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0.0, "num_ctx": 8192}}, timeout=900)
    r.raise_for_status()
    txt = r.json()["message"]["content"].strip().replace("```json", "").replace("```", "")
    try:
        return json.loads(txt)
    except Exception:
        a, b = txt.find("{"), txt.rfind("}")
        return json.loads(txt[a:b + 1]) if a >= 0 and b > a else None


def main():
    entries = [json.loads(l) for l in open(REVIEW, encoding="utf-8")]
    print(f"review entries: {len(entries)}")

    families = {}
    for f in OUT.glob("*.jsonl"):
        families[f.stem] = {json.loads(l)["key"]: json.loads(l)
                            for l in open(f, encoding="utf-8")}

    still_bad = []
    for i, e in enumerate(entries):
        if e.get("reason") == "llm_error" or not e.get("raw"):
            still_bad.append(e)
            continue
        try:
            res = call32b(e)
        except Exception as ex:
            print(f"[{i}] llm error: {ex}")
            still_bad.append(e)
            continue
        if not res or not res.get("rows"):
            still_bad.append(e)
            continue

        family = res.get("family") or e.get("family") or "other"
        problems = norm.validate(res["rows"], e["raw"])
        if problems:
            e["problems_pass2"] = problems[:8]
            still_bad.append(e)
            continue

        for row in res["rows"]:
            key = norm.slug(row.get("name") or row.get("level") or row.get("condition")
                            or row.get("category") or row.get("item") or "")
            families.setdefault(family, {})[key] = {
                "key": key, "_page": e.get("page"), "_validated": True, **row}
        print(f"[{i}] fixed: {family} +{len(res['rows'])}", flush=True)

    for family, rows in families.items():
        with open(OUT / f"{family}.jsonl", "w", encoding="utf-8") as f:
            for rec in rows.values():
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with open(OUT / "review_queue_pass2.jsonl", "w", encoding="utf-8") as f:
        for e in still_bad:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"fixed -> families; still bad: {len(still_bad)}")


if __name__ == "__main__":
    main()