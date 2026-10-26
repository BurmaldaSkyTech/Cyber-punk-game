# scripts/01_extract.py
import json, sys, collections, re
from pathlib import Path
import fitz

PDF_PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "data/raw/cyberpunk_red.pdf")
OUT_DIR = Path("data/extracted")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_boilerplate(doc, max_pages=80, thresh=0.55):
    counter = collections.Counter()
    pages = list(range(min(doc.page_count, max_pages)))
    for i in pages:
        seen = set()
        for line in doc[i].get_text().splitlines():
            s = line.strip()
            if 0 < len(s) <= 50:
                seen.add(re.sub(r"\d+", "#", s).lower())
        for s in seen:
            counter[s] += 1
    n = max(1, len(pages))
    return {k for k, v in counter.items() if v / n >= thresh}


def is_boiler(line, boiler):
    s = re.sub(r"\d+", "#", line.strip()).lower()
    return s in boiler or (line.strip().isdigit() and len(line.strip()) <= 4)


def inside_any_bbox(bbox, bboxes):
    x0, y0, x1, y1 = bbox
    for r in bboxes:
        if x0 >= r[0] - 2 and y0 >= r[1] - 2 and x1 <= r[2] + 2 and y1 <= r[3] + 2:
            return True
    return False


def cells_from_words(table, words):
    try:
        nr, nc = table.row_count, table.col_count
        cells = table.cells
    except Exception:
        return None
    if not cells or len(cells) != nr * nc:
        return None
    rows = [["" for _ in range(nc)] for _ in range(nr)]
    for idx, bbox in enumerate(cells):
        if bbox is None:
            continue
        r, c = divmod(idx, nc)
        x0, y0, x1, y1 = bbox
        sel = []
        for w in words:
            wx = (w[0] + w[2]) / 2
            wy = (w[1] + w[3]) / 2
            if x0 - 1 <= wx <= x1 + 1 and y0 - 1 <= wy <= y1 + 1:
                sel.append(w)
        sel.sort(key=lambda w: (round(w[1] / 3), w[0]))
        rows[r][c] = " ".join(w[4] for w in sel).strip()
    return rows


def drop_empty_cols(rows):
    if not rows:
        return rows
    nc = max(len(r) for r in rows)
    keep = [c for c in range(nc)
            if any((r[c].strip() if c < len(r) else "") for r in rows)]
    if not keep or len(keep) == nc:
        return rows
    return [[(r[c] if c < len(r) else "") for c in keep] for r in rows]


def rows_to_markdown(rows):
    rows = [[("" if c is None else str(c).strip().replace("\n", " ")) for c in r] for r in rows]
    rows = [r for r in rows if any(r)]
    if not rows:
        return ""
    header = rows[0]
    out = ["| " + " | ".join(header) + " |"]
    out.append("|" + "|".join(["---"] * len(header)) + "|")
    for r in rows[1:]:
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))
        out.append("| " + " | ".join(r[:len(header)]) + " |")
    return "\n".join(out)


def page_columns(lines, width):
    mid = width / 2
    left, right, cross, touch = [], [], [], []
    for l in lines:
        x0, y0, x1, y1 = l["bbox"]
        if x1 < mid - 8:
            left.append(l)
        elif x0 > mid + 8:
            right.append(l)
        elif x0 < mid - 8 and x1 > mid + 8:
            cross.append(l)
        else:
            touch.append(l)
    two_col = (len(left) >= 5 and len(right) >= 5
               and len(cross) <= 0.15 * max(1, len(lines)))
    if not two_col:
        return lines, [], []
    col0, col1 = [], list(right)
    for l in left + touch:
        cx = (l["bbox"][0] + l["bbox"][2]) / 2
        (col0 if cx < mid else col1).append(l)
    for c in (col0, col1, cross):
        c.sort(key=lambda l: l["bbox"][1])
    return col0, col1, cross


def merge_dropcaps(lines):
    out = []
    i = 0
    while i < len(lines):
        t = lines[i]["text"].strip()
        if (len(t) == 1 and t.isalpha() and t.isupper()
                and i + 1 < len(lines)
                and lines[i + 1]["text"][:1].islower()):
            merged = dict(lines[i + 1])
            merged["text"] = t + lines[i + 1]["text"].strip()
            out.append(merged)
            i += 2
            continue
        out.append(lines[i])
        i += 1
    return out


def main():
    doc = fitz.open(PDF_PATH)
    boiler = find_boilerplate(doc)
    print(f"boilerplate patterns: {len(boiler)}")

    toc = doc.get_toc()
    (OUT_DIR / "toc.json").write_text(
        json.dumps([{"level": l, "title": t.strip(), "page": p} for l, t, p in toc],
                   ensure_ascii=False, indent=2),
        encoding="utf-8")

    l1 = {}
    for lvl, title, page in toc:
        if lvl == 1:
            l1[title.strip().upper()] = page

    blocks_out, tables_out = [], []
    seq = 0

    for pno in range(doc.page_count):
        page = doc[pno]
        width = page.rect.width
        words = page.get_text("words")

        found = page.find_tables()
        table_bboxes, full_items = [], []
        for t in found.tables:
            rows = cells_from_words(t, words)
            if rows is None:
                try:
                    rows = t.extract()
                except Exception:
                    continue
            rows = [[("" if c is None else str(c).strip().replace("\n", " ")) for c in r] for r in rows]
            rows = [r for r in rows if any(r)]
            rows = drop_empty_cols(rows)
            md = rows_to_markdown(rows)
            if not md:
                continue
            table_bboxes.append(t.bbox)
            tables_out.append({"page": pno + 1, "bbox": list(t.bbox),
                               "markdown": md, "rows": rows})
            full_items.append({"y": t.bbox[1], "kind": "table", "text": md})

        text_lines = []
        d = page.get_text("dict")
        for blk in d.get("blocks", []):
            if blk.get("type", 0) != 0:
                continue
            for line in blk.get("lines", []):
                parts = []
                for span in line.get("spans", []):
                    if inside_any_bbox(span["bbox"], table_bboxes):
                        continue
                    parts.append(span["text"])
                s = "".join(parts).strip()
                if not s:
                    continue
                if is_boiler(s, boiler):
                    continue
                if s.upper() in l1 and (pno + 1) > l1[s.upper()]:
                    continue
                text_lines.append({"bbox": line["bbox"], "text": s})

        col0, col1, full_text = page_columns(text_lines, width)
        col0 = merge_dropcaps(col0)
        col1 = merge_dropcaps(col1)

        full_stream = sorted(
            full_items + [{"y": l["bbox"][1], "kind": "text", "text": l["text"]}
                          for l in full_text],
            key=lambda x: x["y"])

        ordered = ([{"kind": "text", "text": l["text"]} for l in col0]
                   + [{"kind": it["kind"], "text": it["text"]} for it in full_stream]
                   + [{"kind": "text", "text": l["text"]} for l in col1])

        for item in ordered:
            blocks_out.append({"page": pno + 1, "seq": seq,
                               "kind": item["kind"], "text": item["text"]})
            seq += 1

        if (pno + 1) % 50 == 0:
            print(f"processed {pno + 1}/{doc.page_count} pages")

    with open(OUT_DIR / "blocks.jsonl", "w", encoding="utf-8") as f:
        for b in blocks_out:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")

    with open(OUT_DIR / "tables.jsonl", "w", encoding="utf-8") as f:
        for t in tables_out:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    print(f"blocks: {len(blocks_out)}")
    print(f"tables: {len(tables_out)}")


if __name__ == "__main__":
    main()