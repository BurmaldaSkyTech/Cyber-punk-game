# backend/common.py
import re

CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\u0e00-\u0e7f]")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_") or "unknown"


def flat(md):
    return re.sub(r"\s+", "", md).lower()


def digits(md):
    return re.sub(r"\D", "", md)


def flat_cells(md):
    cells = []
    for line in md.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.fullmatch(r"\|[\s:\-|]+\|", line):
            continue
        cells.extend(p.strip() for p in line.strip("|").split("|"))
    return [c for c in cells if c]


def validate(rows, md):
    f, d = flat(md), digits(md)
    problems = []
    for i, row in enumerate(rows or []):
        for k, v in row.items():
            for vv in (v if isinstance(v, list) else [v]):
                if vv is None or isinstance(vv, bool):
                    continue
                s = str(vv)
                compact = re.sub(r"\s+", "", s).lower()
                nums = re.findall(r"\d+", s)
                ok = compact in f or (nums and all(n in d for n in nums) and len(compact) <= 5)
                if not ok:
                    problems.append({"row": i, "field": k, "value": s})
    return problems


def clean(s):
    s = CJK.sub("", s or "")
    s = re.sub(r"掩码部分敏感信息.*", "", s, flags=re.S)
    s = re.sub(r"\b[a-zA-Z]{3,}\b", "", s)  # убрать отдельные латинские слова
    return re.sub(r"\s+", " ", s).strip()