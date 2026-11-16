import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / "backend" / "main.py"
lines = TARGET.read_text(encoding="utf-8").splitlines(keepends=True)


def span(name):
    s = next(i for i, l in enumerate(lines) if l.startswith(f"def {name}"))
    e = next(i for i in range(s + 1, len(lines))
             if lines[i].startswith(("@app.", "def ", "class ")))
    return s, e


def replace(name, txt):
    global lines
    s, e = span(name)
    new = (ROOT / "tools" / txt).read_text(encoding="utf-8").splitlines(keepends=True)
    if new and not new[-1].endswith("\n"):
        new[-1] += "\n"
    lines = lines[:s] + new + ["\n", "\n"] + lines[e:]
    print(f"rebuilt {name}: old lines {s + 1}..{e} -> {len(new)} new lines")


replace("assemble_narration", "assemble_new.txt")
replace("_act_core", "act_new.txt")
TARGET.write_text("".join(lines), encoding="utf-8")
print("backend/main.py rewritten")