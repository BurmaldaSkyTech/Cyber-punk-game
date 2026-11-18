"""Приводит test_wound_thresholds к книжным порогам (стр.187)."""
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
p = ROOT / "tests" / "test_core.py"
src = p.read_text(encoding="utf-8")

NEW = '''def test_wound_thresholds():
    # Книга, стр.187: seriously при hp < ceil(max/2); mortally при hp < 1
    from backend.wounds import get_wound_state

    assert get_wound_state(10, 10) == "unharmed"
    assert get_wound_state(9, 10) == "lightly"
    assert get_wound_state(5, 10) == "lightly"
    assert get_wound_state(4, 10) == "seriously"
    assert get_wound_state(1, 10) == "seriously"
    assert get_wound_state(0, 10) == "mortally"
    assert get_wound_state(-3, 10) == "mortally"
    assert get_wound_state(20, 40) == "lightly"
    assert get_wound_state(19, 40) == "seriously"
'''

tree = ast.parse(src)
node = next(n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "test_wound_thresholds")
lines = src.splitlines(keepends=True)
src = "".join(lines[:node.lineno - 1]) + NEW + "".join(lines[node.end_lineno:])
p.write_text(src, encoding="utf-8")
print("test_wound_thresholds: пороги приведены к книге")