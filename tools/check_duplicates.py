"""Ищет дубли определений верхнего уровня — мёртвый код, оставшийся после патчей."""
import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = 0
for p in sorted((ROOT / "backend").glob("*.py")):
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"))
    except SyntaxError as e:
        print(f"{p.name}: SYNTAX {e.lineno}")
        bad += 1
        continue
    seen = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            seen.setdefault(node.name, []).append(node.lineno)
    dups = {k: v for k, v in seen.items() if len(v) > 1}
    if dups:
        print(f"{p.name}:")
        for k, lns in dups.items():
            print(f"  {k}: строки {lns} — исполняется последняя")
            bad += 1
print(f"дублей: {bad}")
sys.exit(1 if bad else 0)