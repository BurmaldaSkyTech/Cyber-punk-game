# scripts/02_chunk.py
import json, re
from pathlib import Path

IN_DIR = Path("data/extracted")
OUT = Path("data/chunks")
OUT.mkdir(parents=True, exist_ok=True)

MAX_CHARS = 2200
MIN_CHARS = 350


def load_toc():
    p = IN_DIR / "toc.json"
    if not p.exists():
        return []
    toc = json.loads(p.read_text(encoding="utf-8"))
    return sorted([e for e in toc if e.get("title")], key=lambda e: e["page"])


def is_heading(b):
    if b["kind"] != "text":
        return False
    t = b["text"].strip()
    if not (2 <= len(t) <= 90):
        return False
    if t.endswith((".", ",", ";", ":")):
        return False
    words = re.findall(r"[A-Za-zА-Яа-яЁё0-9\-\+]+", t)
    if not words or len(words) > 12:
        return False
    caps = sum(1 for w in words if len(w) > 1 and w.isupper())
    titled = sum(1 for w in words if w[:1].isupper())
    return caps >= 1 or (titled / len(words)) >= 0.7


class PathStack:
    def __init__(self):
        self.stack = {}

    def set(self, level, title):
        self.stack[level] = title
        for k in list(self.stack):
            if k > level:
                del self.stack[k]

    def crumb(self):
        return " > ".join(self.stack[k] for k in sorted(self.stack))


def main():
    toc = load_toc()
    blocks = [json.loads(l) for l in open(IN_DIR / "blocks.jsonl", encoding="utf-8")]
    norm_toc = [(e, e["title"].lower().strip()) for e in toc]
    stack = PathStack()
    ti = 0

    chunks = []
    cur = {"text": [], "page_start": None, "page_end": None,
           "crumb": "", "kind": "text"}

    def flush():
        nonlocal cur
        if cur["text"]:
            text = "\n".join(cur["text"]).strip()
            if len(text) >= MIN_CHARS or cur["kind"] == "table":
                chunks.append({
                    "text": text,
                    "crumb": cur["crumb"],
                    "page_start": cur["page_start"],
                    "page_end": cur["page_end"],
                    "kind": cur["kind"],
                    "chars": len(text),
                })
        cur = {"text": [], "page_start": None, "page_end": None,
               "crumb": stack.crumb(), "kind": "text"}

    for b in blocks:
        page = b["page"]

        while ti < len(norm_toc) and norm_toc[ti][0]["page"] <= page:
            e = norm_toc[ti][0]
            stack.set(e["level"], e["title"].strip())
            ti += 1
            cur["crumb"] = stack.crumb()

        heading = is_heading(b)

        if b["kind"] == "table":
            flush()
            cur["kind"] = "table"
            cur["crumb"] = stack.crumb()
            cur["text"].append(b["text"])
            cur["page_start"] = cur["page_end"] = page
            flush()
            continue

        if heading:
            flush()
            cur["crumb"] = stack.crumb() or b["text"].strip()

        if cur["page_start"] is None:
            cur["page_start"] = page
        cur["page_end"] = page
        cur["text"].append(b["text"])

        if sum(len(t) for t in cur["text"]) > MAX_CHARS:
            flush()

    flush()

    with open(OUT / "chunks.jsonl", "w", encoding="utf-8") as f:
        for i, c in enumerate(chunks):
            c["id"] = f"chunk_{i:05d}"
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"chunks: {len(chunks)}")
    print(f"avg chars: {sum(c['chars'] for c in chunks) // max(1, len(chunks))}")


if __name__ == "__main__":
    main()