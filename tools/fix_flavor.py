import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / "backend" / "main.py"
src = TARGET.read_text(encoding="utf-8")
lines = src.splitlines(keepends=True)
tree = ast.parse(src)

parts = {}
key = None
for chunk in (ROOT / "tools" / "flavor_new.txt").read_text(encoding="utf-8").split("# === "):
    if not chunk.strip():
        continue
    name, _, body = chunk.partition(" ===\n")
    parts[name.strip()] = body


def span_of(node):
    return node.lineno - 1, node.end_lineno


replacements = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "NARR_FLAVOR_SYS" for t in node.targets):
        replacements.append((span_of(node), parts["CONST"]))
    elif isinstance(node, ast.FunctionDef) and node.name == "_clean_flavor":
        replacements.append((span_of(node), parts["CLEAN"]))
    elif isinstance(node, ast.FunctionDef) and node.name == "sanitize_flavor":
        replacements.append((span_of(node), parts["SANITIZE"]))

for (s, e), text in sorted(replacements, reverse=True):
    new = text.splitlines(keepends=True)
    if new and not new[-1].endswith("\n"):
        new[-1] += "\n"
    lines = lines[:s] + new + lines[e:]

src = "".join(lines)

old_prev = '    prev_short = (st["log"][-1]["narration"][:160] if st["log"] else "")'
new_prev = '    prev_short = (st["log"][-1]["text"][:120] if st["log"] else "")'
assert src.count(old_prev) == 1, "prev_short anchor not found"
src = src.replace(old_prev, new_prev)

old_call = "    narration = assemble_narration(mech, actor_name, sanitize_flavor(flavor_raw, shots_n), extra=extra)"
new_call = ("    narration = assemble_narration(mech, actor_name, sanitize_flavor(\n"
            "        flavor_raw, shots_n,\n"
            "        npc_names=[n[\"name\"] for n in st[\"npcs\"]],\n"
            "        actor_name=actor_name, declared=req.text), extra=extra)")
assert src.count(old_call) == 1, "sanitize call anchor not found"
src = src.replace(old_call, new_call)

old_tail = '            f"Выстрелов NPC: {shots_n}\\nВерни JSON flavor."}'
new_tail = ('            f"Выстрелов NPC: {shots_n}\\n"\n'
            '            f"Запрещено вводить новые предметы и контейнеры; NPC ничего не передаёт.\\n"\n'
            '            f"Верни JSON flavor."}')
assert src.count(old_tail) == 1, "flavor user-content anchor not found"
src = src.replace(old_tail, new_tail)

TARGET.write_text(src, encoding="utf-8")
print("flavor pipeline rebuilt: no invented objects, player-only action, no name leaks, no repetition loop")