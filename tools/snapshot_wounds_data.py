"""Снимок backend/wounds.py + инвентарь уже извлечённых книжных данных."""
import ast
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "SNAPSHOT_WOUNDS_DATA.md"

WANTED = ["skills_full", "cyberware_full", "martial_arts", "martial_moves",
          "weapons_full", "armor_full", "drugs", "poisons", "programs",
          "cyberdecks", "architectures", "vehicles", "enemies", "factions"]


def dump_wounds(out):
    p = ROOT / "backend" / "wounds.py"
    if not p.exists():
        out.append("backend/wounds.py NOT FOUND\n")
        print("wounds.py не найден")
        return
    src = p.read_text(encoding="utf-8")
    out.append(f"\n\n===== backend/wounds.py ({len(src.splitlines())} строк) =====\n")
    out.append(src if len(src.splitlines()) <= 450 else "")
    if len(src.splitlines()) > 450:
        tree = ast.parse(src)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Assign)):
                out.append(f"\n--- {getattr(node, 'name', 'assign')} ---\n")
                out.append(ast.get_source_segment(src, node) or "")
    print(f"wounds.py: {len(src.splitlines())} строк")


def inventory(out):
    data = ROOT / "data"
    if not data.is_dir():
        out.append("\n\ndata/ NOT FOUND\n")
        return
    files = sorted(data.rglob("*.json"))
    out.append(f"\n\n===== ИНВЕНТАРЬ data/ ({len(files)} json) =====\n")
    found = {}
    for p in files:
        rel = p.relative_to(ROOT)
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            out.append(f"\n--- {rel} — ОШИБКА ЧТЕНИЯ: {e}\n")
            continue
        if isinstance(obj, dict):
            keys = list(obj.keys())
            shape = f"dict, {len(keys)} ключей"
            sample = {k: obj[k] for k in keys[:2]}
        elif isinstance(obj, list):
            shape = f"list, {len(obj)} записей"
            sample = obj[:2]
        else:
            shape, sample = type(obj).__name__, obj
        out.append(f"\n--- {rel} ({p.stat().st_size} байт) — {shape} ---\n")
        if isinstance(obj, dict):
            out.append("ключи: " + ", ".join(map(str, keys[:40])) + "\n")
        out.append("образец: " + json.dumps(sample, ensure_ascii=False)[:900] + "\n")
        stem = p.stem.lower()
        for w in WANTED:
            if w in stem:
                found[w] = str(rel)
        print(f"  {rel}: {shape}")
    out.append("\n\n===== ПОКРЫТИЕ КАТАЛОГА =====\n")
    for w in WANTED:
        out.append(f"{w}: {found.get(w, 'НЕ НАЙДЕН')}\n")
    print("покрытие:", ", ".join(f"{w}={'ok' if w in found else '—'}" for w in WANTED))


if __name__ == "__main__":
    out = []
    dump_wounds(out)
    inventory(out)
    OUT.write_text("".join(out), encoding="utf-8")
    print(f"SNAPSHOT_WOUNDS_DATA.md записан -> {OUT}")