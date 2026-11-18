"""Удаляет РАННИЕ дубли определений верхнего уровня, оставляя последнюю версию.

Без декораторов это поведение-сохраняющая операция: Python и так исполняет
последнюю. С декораторами FastAPI это ИСПРАВЛЕНИЕ: маршрут обслуживала первая
(старая) регистрация. Перед записью делается .bak.
"""
import ast
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = ["backend/db.py", "backend/engine.py", "backend/main.py", "backend/netrunning.py"]
APPLY = "--apply" in sys.argv


def span(node):
    start = node.lineno
    for d in getattr(node, "decorator_list", []) or []:
        start = min(start, d.lineno)
    return start - 1, node.end_lineno


def decorators_src(src_lines, node):
    out = []
    for d in getattr(node, "decorator_list", []) or []:
        out.append(src_lines[d.lineno - 1].strip())
    return out


total = 0
for rel in FILES:
    path = ROOT / rel
    if not path.exists():
        continue
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    groups = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            groups.setdefault(node.name, []).append(node)

    cuts = []
    for name, nodes in groups.items():
        if len(nodes) < 2:
            continue
        keep = nodes[-1]
        for dead in nodes[:-1]:
            a, b = span(dead)
            cuts.append((a, b))
            total += 1
            decs = decorators_src(lines, dead)
            print(f"{rel}: {name} — снос строк {a + 1}..{b}, остаётся {keep.lineno}")
            for d in decs:
                print(f"    декоратор: {d}  (маршрут перейдёт к новой версии)")

    if not cuts:
        continue
    if APPLY:
        shutil.copyfile(path, path.with_suffix(".py.bak"))
        for a, b in sorted(cuts, reverse=True):
            lines = lines[:a] + lines[b:]
        path.write_text("".join(lines), encoding="utf-8")
        print(f"{rel}: записано, бэкап {path.name}.bak")

print(f"\nдублей к сносу: {total}; режим {'APPLY' if APPLY else 'DRY-RUN'}")