"""Проверяет синтаксис всех .py в backend/tools/tests. Печатает файл:строку ошибки."""
import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = 0
total = 0
for folder in ("backend", "tools", "tests"):
    for p in sorted((ROOT / folder).glob("*.py")):
        total += 1
        try:
            ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError as e:
            bad += 1
            print(f"FAIL {folder}/{p.name}:{e.lineno} — {e.msg}")
            line = (p.read_text(encoding="utf-8").splitlines() or [""])[max(0, (e.lineno or 1) - 1)]
            print(f"     {line.strip()[:100]}")
print(f"проверено {total}, сломано {bad}")
sys.exit(1 if bad else 0)