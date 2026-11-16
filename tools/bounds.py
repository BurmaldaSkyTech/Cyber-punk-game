import pathlib

lines = pathlib.Path("backend/main.py").read_text(encoding="utf-8").splitlines()
s = next(i for i, l in enumerate(lines) if l.startswith("def _act_core"))
e = next(i for i in range(s + 1, len(lines))
         if lines[i].startswith(("@app.", "def ", "class ")))
body = [l for l in lines[s:e] if l.strip()]
print(f"_act_core: строки {s + 1}..{e}")
print("последняя строка тела:", repr(body[-1]))
print("следующая top-level строка:", repr(lines[e]))
assert body[-1].strip() == "}", "тело функции должно заканчиваться закрывающей скобкой return"
print("ORPHAN-CHECK: OK")