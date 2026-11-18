"""1) /creation/options принимает method; 2) /creation/roll_stats;
3) NPC лобби приводятся к книжному масштабу HP и получают stats/skills."""
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# --- engine.book_npc ---
ep = ROOT / "backend" / "engine.py"
es = ep.read_text(encoding="utf-8")
if "def book_npc(" not in es:
    es = es.rstrip() + '''


def book_npc(n):
    """NPC с книжным HP и боевыми stats/skills (для встречных бросков)."""
    from backend import rules_tables
    d = dict(n)
    hostile = _is_hostile(d)
    d.setdefault("stats", {"REF": 6, "DEX": 5, "BODY": 6, "WILL": 5} if hostile
                 else {"REF": 4, "DEX": 4, "BODY": 4, "WILL": 5})
    d.setdefault("skills", {"handgun": 4, "evasion": 3} if hostile
                 else {"handgun": 2, "evasion": 2})
    new_max = int(rules_tables.max_hp(d["stats"]))
    old_max = int(d.get("max_hp") or 0)
    if old_max != new_max and new_max > 0:
        ratio = (int(d.get("hp", old_max)) / old_max) if old_max else 1.0
        d["max_hp"] = new_max
        d["hp"] = max(0, min(new_max, int(round(new_max * ratio))))
    return d
'''
    ep.write_text(es, encoding="utf-8")
    print("engine: +book_npc")

# --- main.py ---
mp = ROOT / "backend" / "main.py"
src = mp.read_text(encoding="utf-8")

NEW_OPTIONS = '''def creation_options(role: str = None, method: str = "complete_package"):
    from backend import creation
    return creation.options(role, method)
'''
tree = ast.parse(src)
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "creation_options")
lines = src.splitlines(keepends=True)
src = "".join(lines[:node.lineno - 1]) + NEW_OPTIONS + "".join(lines[node.end_lineno:])
print("main: creation_options принимает method")

if "def creation_roll_stats(" not in src:
    src = src.rstrip() + '''


@app.post("/creation/roll_stats")
def creation_roll_stats():
    from backend import creation
    return creation.roll_stats()
'''
    print("main: +/creation/roll_stats")

old_npcs = '"npcs": [dict(n) for n in DEFAULT_SCENARIO["npcs"]],'
new_npcs = '"npcs": [engine.book_npc(n) for n in DEFAULT_SCENARIO["npcs"]],'
if old_npcs in src:
    src = src.replace(old_npcs, new_npcs)
    print("main: NPC лобби через book_npc")
else:
    print("main: якорь npcs не найден — проверь lobby_create вручную")

mp.write_text(src, encoding="utf-8")