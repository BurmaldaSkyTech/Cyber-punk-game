"""Убирает жёсткие rules.get(..., house=None) из engine: книга не подтверждена —
работаем на домашней карте навыков/штрафов, а не падаем."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# --- rules.py: добавляем get_optional, если её нет ---
rp = ROOT / "backend" / "rules.py"
rsrc = rp.read_text(encoding="utf-8")
if "def get_optional(" not in rsrc:
    rsrc += '''

def get_optional(pack, key, default=None):
    """Значение из книги, если подтверждено; иначе default. Никогда не бросает."""
    e = entry(pack, key)
    if e and e.get("verified") and e.get("value") is not None:
        return e["value"]
    return default
'''
    rp.write_text(rsrc, encoding="utf-8")
    print("rules.py: +get_optional")
else:
    print("rules.py: get_optional уже есть")

# --- engine.py: мягкие fallback ---
ep = ROOT / "backend" / "engine.py"
src = ep.read_text(encoding="utf-8")

old_map = '''    skill_stat = rules.get("creation", "skill_list", house=None)
    if isinstance(skill_stat, list):
        mapped = {s["key"]: s["stat"] for s in skill_stat if isinstance(s, dict)}
        stat_key = mapped.get(skill, SKILL_STAT.get(skill, judge.get("stat", "COOL")))
    else:
        stat_key = SKILL_STAT.get(skill, judge.get("stat", "COOL"))
'''
new_map = '''    stat_key = SKILL_STAT.get(skill, judge.get("stat", "COOL"))
    book_skills = rules.get_optional("creation", "skill_list")
    if isinstance(book_skills, list):
        mapped = {s["key"]: s["stat"] for s in book_skills
                  if isinstance(s, dict) and s.get("key") and s.get("stat")}
        stat_key = mapped.get(skill, stat_key)
    elif isinstance(book_skills, dict):
        stat_key = book_skills.get(skill, stat_key)
'''
assert src.count(old_map) == 1, "не найден блок карты навык->стат"
src = src.replace(old_map, new_map)

for key in ["wound_penalties", "range_dv", "ranged_defense"]:
    old = f'rules.get("combat", "{key}", house=None)'
    new = f'rules.get_optional("combat", "{key}")'
    n = src.count(old)
    if n:
        src = src.replace(old, new)
    print(f"engine.py: {key} -> get_optional ({n} замен)")

ep.write_text(src, encoding="utf-8")
print("engine.py rewritten")