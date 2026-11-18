"""Снимок модулей Scripts/ и карта импортов engine. Пишет SNAPSHOT_SCRIPTS.md."""
import ast
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
CANDIDATES = ["Scripts", "scripts", "backend/Scripts", "backend/scripts"]

TARGETS = {
    "apply_damage", "get_wound_state", "get_wound_penalty", "death_save",
    "roll_d10", "roll_dice", "skill_check", "critical_injury",
    "roll_critical_injury", "apply_critical_injury",
    "WOUND_STATES", "WOUND_PENALTIES", "CRITICAL_INJURIES", "CRIT_TABLE",
    "CRITICAL_INJURY_TABLE", "MOVES",
}


def find_dir():
    for c in CANDIDATES:
        p = ROOT / c
        if p.is_dir():
            return p
    return None


def blocks(src, tree):
    found, surface = {}, []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            surface.append(node.name)
            if node.name in TARGETS:
                found[node.name] = ast.get_source_segment(src, node)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    surface.append(t.id)
                    if t.id in TARGETS:
                        found[t.id] = ast.get_source_segment(src, node)
    return found, surface


def main():
    out = []
    d = find_dir()
    if d is None:
        print("Папка Scripts не найдена. Кандидаты:", CANDIDATES)
        return
    print(f"Каталог: {d.relative_to(ROOT)}")
    out.append(f"# Scripts snapshot: {d.relative_to(ROOT)}\n")

    files = sorted(d.rglob("*.py"))
    total_hits = 0
    for p in files:
        rel = p.relative_to(ROOT)
        src = p.read_text(encoding="utf-8", errors="replace")
        out.append(f"\n\n===== {rel} ({len(src.splitlines())} строк) =====\n")
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            out.append(f"SYNTAX ERROR line {e.lineno}: {e.msg}\n")
            print(f"  FAIL {rel}: строка {e.lineno} — {e.msg}")
            continue
        found, surface = blocks(src, tree)
        total_hits += len(found)
        out.append(f"\n--- поверхность модуля ---\n{', '.join(surface) or '—'}\n")
        for name in sorted(found):
            out.append(f"\n--- {name} ---\n{found[name]}\n")
        print(f"  {rel}: {len(found)} целевых, {len(surface)} символов")

    eng = ROOT / "backend" / "engine.py"
    if eng.exists():
        out.append("\n\n===== ИМПОРТЫ backend/engine.py =====\n")
        for i, line in enumerate(eng.read_text(encoding="utf-8").splitlines(), 1):
            if re.match(r"\s*(from|import)\s", line) or "sys.path" in line:
                out.append(f"{i}: {line}\n")

    dest = ROOT / "SNAPSHOT_SCRIPTS.md"
    dest.write_text("".join(out), encoding="utf-8")
    print(f"SNAPSHOT_SCRIPTS.md записан, целевых функций найдено: {total_hits}")


if __name__ == "__main__":
    main()