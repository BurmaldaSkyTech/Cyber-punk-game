"""Крит-фолбэк: один бросок 2d6, выбор согласован с локацией, +отчёт покрытия."""
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
p = ROOT / "backend" / "wounds_book.py"
src = p.read_text(encoding="utf-8")

NEW = '''def roll_critical_injury(location="auto", damage_type="bullet", rng=None):
    # Один бросок 2d6: сначала книжная таблица, иначе домарка по той же локации
    rng = rng or random
    roll = rng.randint(1, 6) + rng.randint(1, 6)
    table = _book_table(location)
    if table and table.get(str(roll)):
        key = "critical_injury_table_head" if location == "head" else "critical_injury_table_body"
        prov = rules.provenance("combat", key)
        return {"roll": roll, "location": location, "name": table[str(roll)],
                "source": "book", "page": prov.get("page")}
    name = _house_entry(location, damage_type, roll)
    return {"roll": roll, "location": location,
            "name": name or "Критическая травма: эффект уточняется",
            "source": "house",
            "note": "в книжной таблице " + str(location) + " нет броска " + str(roll)}
'''

HELPERS = '''

HEAD_WORDS = ("голов", "череп", "глаз", "мозг", "челюст", "оглуш", "контуз", "сознани")
BODY_WORDS = ("рук", "ног", "палец", "рёбр", "ребр", "лёгк", "легк", "живот",
              "артери", "ожог", "обугл", "кровотеч", "плеч")


def _house_table(damage_type):
    raw = getattr(base, "CRITICAL_INJURIES", {}) or {}
    norm = {str(k).strip(): v for k, v in raw.items()}
    return norm.get(str(damage_type).strip()) or norm.get("bullet") or {}


def _house_entry(location, damage_type, roll):
    table = _house_table(damage_type)
    if not table:
        return None
    words = HEAD_WORDS if location == "head" else BODY_WORDS
    pool = [v for v in table.values() if any(w in str(v).lower() for w in words)]
    if not pool:
        pool = list(table.values())
    return pool[(roll - 2) % len(pool)] if pool else None


def crit_table_coverage():
    out = {}
    for loc, key in (("head", "critical_injury_table_head"),
                     ("body", "critical_injury_table_body")):
        t = rules.get_optional("combat", key) or {}
        have = sorted(int(k) for k in t.keys() if str(k).isdigit())
        out[loc] = {"have": have,
                    "missing": [r for r in range(2, 13) if r not in have],
                    "verified": rules.verified("combat", key)}
    return out
'''

tree = ast.parse(src)
node = next(n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "roll_critical_injury")
lines = src.splitlines(keepends=True)
src = "".join(lines[:node.lineno - 1]) + NEW + "".join(lines[node.end_lineno:])
if "def crit_table_coverage(" not in src:
    src = src.rstrip() + "\n" + HELPERS
p.write_text(src, encoding="utf-8")
print("wounds_book: фолбэк по локации, один бросок, +crit_table_coverage")