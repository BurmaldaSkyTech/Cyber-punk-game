"""1) bodyplate -> metalgear в rules_tables.
2) Штраф брони (REF/DEX/MOVE) наконец влияет на бросок игрока."""
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# --- rules_tables.armor_table: алиас bodyplate ---
rp = ROOT / "backend" / "rules_tables.py"
rsrc = rp.read_text(encoding="utf-8")
new_armor = '''def armor_table(base):
    out = {k: dict(v) for k, v in base.items()}
    book = rules.get_optional("armor", "table")
    if isinstance(book, dict):
        for k, v in book.items():
            if v.get("is_shield"):
                continue
            cur = out.setdefault(k, {})
            if "sp" in v:
                cur["sp"] = v["sp"]
            pen = v.get("penalty") or {}
            cur["penalty"] = pen.get("value", 0)
            cur["penalty_stats"] = pen.get("stats", [])
            if v.get("price") is not None:
                cur["price"] = v["price"]
        if "metalgear" in out and "bodyplate" in out:
            out["bodyplate"].update(out["metalgear"])
            out["bodyplate"]["book_alias"] = "metalgear"
    return out
'''
tree = ast.parse(rsrc)
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "armor_table")
lines = rsrc.splitlines(keepends=True)
rsrc = "".join(lines[:node.lineno - 1]) + new_armor + "".join(lines[node.end_lineno:])
rp.write_text(rsrc, encoding="utf-8")
print("rules_tables.armor_table: +bodyplate alias")

# --- engine.resolve_check: штраф брони ---
ep = ROOT / "backend" / "engine.py"
src = ep.read_text(encoding="utf-8")
tree = ast.parse(src)
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "resolve_check")
lines = src.splitlines(keepends=True)
body = "".join(lines[node.lineno - 1:node.end_lineno])

anchor_mods = [
    '    mods = wound_pen.get(wound_state, 0) if isinstance(wound_pen, dict) else get_wound_penalty(wound_state)\n',
    '    mods = get_wound_penalty(wound_state)\n',
]
hit = next((a for a in anchor_mods if a in body), None)
assert hit, "не найден mods-anchor в resolve_check"
inject = '''    armor_rec = ARMOR.get(actor.get("armor") or "", {}) or {}
    armor_pen = int(armor_rec.get("penalty", 0) or 0)
    pen_stats = armor_rec.get("penalty_stats") or ["REF", "DEX", "MOVE"]
    if armor_pen and stat_key in pen_stats:
        mods += armor_pen
'''
if "armor_pen" not in body:
    body = body.replace(hit, hit + inject)

anchor_check = '    mech = skill_check(stat, sk_lvl, dv, mods)\n'
assert anchor_check in body, "не найден skill_check-anchor"
if 'mech["armor_penalty"]' not in body:
    body = body.replace(
        anchor_check,
        anchor_check + '    mech["armor_penalty"] = armor_pen if stat_key in pen_stats else 0\n')

src = "".join(lines[:node.lineno - 1]) + body + "".join(lines[node.end_lineno:])
ep.write_text(src, encoding="utf-8")
print("engine.resolve_check: +armor penalty on REF/DEX/MOVE")