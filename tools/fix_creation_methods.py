import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
parts, key = {}, None
for chunk in (ROOT / "tools" / "creation_new.txt").read_text(encoding="utf-8").split("# === "):
    if not chunk.strip():
        continue
    name, _, body = chunk.partition(" ===\n")
    parts[name.strip()] = body

p = ROOT / "backend" / "creation.py"
src = p.read_text(encoding="utf-8")

for fname in ("build", "options", "limits"):
    tree = ast.parse(src)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == fname)
    lines = src.splitlines(keepends=True)
    new = parts[fname.upper()].splitlines(keepends=True)
    if new and not new[-1].endswith("\n"):
        new[-1] += "\n"
    src = "".join(lines[:node.lineno - 1]) + "".join(new) + "\n\n" + "".join(lines[node.end_lineno:])
    print(f"creation.{fname} заменён")

if "def methods(" not in src:
    src = src.rstrip() + "\n\n\n" + parts["METHODS"]
    print("creation: +methods/roll_stats")

p.write_text(src, encoding="utf-8")