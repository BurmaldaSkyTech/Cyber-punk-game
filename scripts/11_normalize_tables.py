# scripts/11_normalize_tables.py  (v2: deterministic unwrap + regex skills)
import json, os, re, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "data" / "extracted" / "tables.jsonl"
BLOCKS = ROOT / "data" / "extracted" / "blocks.jsonl"
OUT = ROOT / "data" / "normalized"
OUT.mkdir(parents=True, exist_ok=True)
REVIEW = OUT / "review_queue.jsonl"

OLLAMA = "http://localhost:11434/api/chat"
MODEL = os.environ.get("NORM_MODEL", "qwen2.5:7b-instruct")

LLM_FAMILIES = ["cyberware", "gear", "drugs", "vehicles", "economy", "net_programs",
                "critical_injuries", "role_abilities", "interface_abilities",
                "lifepath", "other"]

SPECS = {
    "dv_table": [("Difficulty", "level"), ("Description", "description"), ("DV", "dv")],
    "armor": [("Armor Type", "name"), ("Armor Description", "description"),
              ("Damage Stopping Power", "sp"), ("Armor Penalty", "penalty"),
              ("Cost", "price_eb")],
    "weapons": [("Weapon", "name"), ("Description and Data", "description"),
                ("Cost", "price_eb")],
    "melee_types": [("Melee Weapon Type", "name"), ("Example Melee Weapons", "examples"),
                    ("Damage", "damage")],
    "condition_mods": [("Condition", "condition"), ("Mod Value", "mod")],
    "wound_states": [("Wound State", "name"), ("Threshold", "threshold"),
                     ("Wound Effect", "effect"), ("Stabilization DV", "stabilization_dv")],
}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_") or "unknown"


def flat(md):
    return re.sub(r"\s+", "", md).lower()


def digits(md):
    return re.sub(r"\D", "", md)


def ints(s):
    d = re.findall(r"-?\d+", s or "")
    return int(d[0]) if d else None


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
        if not isinstance(row, dict):
            continue
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


def unwrap(md, markers):
    cells = flat_cells(md)
    found, used = [], set()
    for m in markers:
        ml = m.lower()
        hit = None
        for i, c in enumerate(cells):
            if i in used:
                continue
            if ml in c.lower():
                hit = i
                break
        if hit is None:
            return None
        used.add(hit)
        found.append((m, hit))
    found.sort(key=lambda x: x[1])
    segs = {}
    for j, (m, i) in enumerate(found):
        end = found[j + 1][1] if j + 1 < len(found) else len(cells)
        segs[m] = cells[i + 1:end]
    return segs


def spec_records(md, spec):
    segs = unwrap(md, [m for m, _ in spec])
    if segs is None:
        return None, "markers not found"
    present = [(m, f) for m, f in spec if m in segs]
    lens = [len(segs[m]) for m, _ in present]
    note = f"segment lengths {min(lens)}..{max(lens)}" if max(lens) - min(lens) > 1 else None
    rows = []
    for i in range(min(lens)):
        rec = {}
        for m, f in present:
            rec[f] = segs[m][i] if i < len(segs[m]) else None
        rows.append(rec)
    return rows, note


def parse_weapon(rec):
    d = rec.get("description") or ""
    rec["damage"] = (re.search(r"\d+d\d+(?:\s*\+\s*\d+)?", d) or [None])[0]
    rec["ammo"] = ints((re.search(r"(\d+)\s*(?:rounds|bullets|shots|charges)", d, re.I) or [None, None])[1])
    rof = re.search(r"ROF\s*(\d+)|(\d+)\s*ROF", d, re.I)
    rec["rof"] = ints(rof.group(1) or rof.group(2)) if rof else None
    rec["range_m"] = ints((re.search(r"(\d+)\s*m/yds?", d, re.I) or [None, None])[1])
    return rec


def pre_classify(md, page):
    cells = flat_cells(md)
    if not cells:
        return None
    low = [c.lower() for c in cells]
    joined = " ".join(low[:40])
    if low[0] == "roll" and any(k in joined for k in [
            "what are you like", "clothing style", "life goals", "moral compass",
            "who?", "where?", "what happened", "cultural region", "affectation",
            "family background", "friends", "enemy", "tragic love", "fashion"]):
        return "lifepath"
    if low[0] in ("int", "ref", "dex", "tech", "cool", "will", "luck", "move", "body", "emp"):
        return "stat_rolls"
    if page == 130 and "simple" in low and "legendary" in low:
        return "dv_table"
    if "wound state" in low:
        return "wound_states"
    if "condition" in low and "mod value" in low:
        return "condition_mods"
    if "roll (2d6)" in low and "injury" in low:
        return "critical_injuries"
    if "armor type" in low and any("stopping power" in c for c in low):
        return "armor"
    if "weapon" in low and "description and data" in low:
        return "weapons"
    if "melee weapon type" in low:
        return "melee_types"
    return None


SCHEMAS = """
cyberware: name, slot, humanity_loss, price_eb
gear: name, description, price_eb
drugs: name, effect, duration, dv, price_eb
vehicles: name, type, sdp, seats, speed_mph, price_eb
net_programs: name, cls, spd, atk, def, rez, effect, cost
critical_injuries: region, roll, name, effect, quick_fix, treatment
role_abilities: role, ability, effect
interface_abilities: name, effect
economy: category, item, price_eb
lifepath / other: любые ключи, переносить как есть
"""

SYS = f"""Ты — нормализатор таблиц книги Cyberpunk RED.
Выбери family ТОЛЬКО из списка: {LLM_FAMILIES}.
Выдай строки как JSON-объекты со ключами схемы. КОПИРУЙ значения ДОСЛОВНО.
Нет значения -> null. Ничего не выдумывай и не вычисляй.
Верни ТОЛЬКО JSON: {{"family": str, "rows": [ ... ]}}
СХЕМЫ:
{SCHEMAS}"""


def llm_normalize(md, pin=None):
    sys_prompt = SYS if not pin else (
        f"Ты — нормализатор таблиц. Family УЖЕ выбрана: {pin}. "
        f"Выдай строки JSON со ключами схемы этой family, копируя значения ДОСЛОВНО. "
        f"Верни ТОЛЬКО JSON: {{\"family\": \"{pin}\", \"rows\": [ ... ]}}\nСХЕМА:\n{SCHEMAS}")
    r = requests.post(OLLAMA, json={
        "model": MODEL, "stream": False, "format": "json",
        "messages": [{"role": "system", "content": sys_prompt},
                     {"role": "user", "content": f"TABLE:\n{md[:4000]}"}],
        "options": {"temperature": 0.0, "num_ctx": 8192}}, timeout=300)
    r.raise_for_status()
    txt = r.json()["message"]["content"].strip().replace("```json", "").replace("```", "")
    try:
        return json.loads(txt)
    except Exception:
        a, b = txt.find("{"), txt.rfind("}")
        return json.loads(txt[a:b + 1]) if a >= 0 and b > a else {"family": "other", "rows": []}


def extract_skill_stats():
    pat = re.compile(
        r"^([A-Za-z][A-Za-z()/&,'\- ]{2,40}?)(\s*\(x2\))?\s*\.+\s*"
        r"(INT|REF|DEX|TECH|COOL|WILL|LUCK|MOVE|BODY|EMP)$")
    out = {}
    for line in open(BLOCKS, encoding="utf-8"):
        b = json.loads(line)
        if b.get("kind") != "text":
            continue
        for ln in b["text"].splitlines():
            m = pat.match(ln.strip())
            if m:
                out[slug(m.group(1))] = {"name": m.group(1).strip(), "stat": m.group(3),
                                         "x2": bool(m.group(2)), "_page": b["page"]}
    return out


def main():
    tables = [json.loads(l) for l in open(TABLES, encoding="utf-8")]
    print(f"tables: {len(tables)}")

    by_family, review = {}, []

    for ti, t in enumerate(tables):
        md, page = t.get("markdown", ""), t.get("page", 0)
        if len(md) < 20:
            continue

        pre = pre_classify(md, page)
        rows, note, family = None, None, None

        if pre in SPECS:
            family = pre
            rows, note = spec_records(md, SPECS[pre])
            if rows is None:
                family, rows, note = None, None, "spec markers failed"
        elif pre in ("lifepath", "stat_rolls"):
            family = pre
            rows, note = [{"raw": c} for c in flat_cells(md)], None
        elif pre == "critical_injuries":
            region = "head" if any(k in md.lower() for k in ["lost eye", "brain injury", "broken jaw"]) else "body"
            res = llm_normalize(md, pin="critical_injuries")
            family, rows = "critical_injuries", [r for r in (res.get("rows") or []) if isinstance(r, dict)]
            for r in rows:
                r["region"] = region
        elif pre is None:
            try:
                res = llm_normalize(md)
            except Exception as e:
                review.append({"page": page, "reason": f"llm_error: {e}", "raw": md[:300]})
                continue
            family = res.get("family") if res.get("family") in LLM_FAMILIES else "other"
            rows = [r for r in (res.get("rows") or []) if isinstance(r, dict)]
        else:
            family, rows = pre, [{"raw": c} for c in flat_cells(md)]

        if not rows:
            review.append({"page": page, "reason": note or "no rows", "raw": md[:300]})
            continue

        if family == "dv_table":
            for r in rows:
                r["dv"] = ints(r.get("dv"))
                r["level"] = (r.get("level") or "").strip().lower()
        if family == "armor":
            for r in rows:
                r["sp"] = ints(r.get("sp"))
        if family == "wound_states":
            for r in rows:
                r["stabilization_dv"] = ints(r.get("stabilization_dv"))
        if family == "weapons":
            rows = [parse_weapon(r) for r in rows]
        if family == "condition_mods":
            for r in rows:
                r["mod"] = ints(r.get("mod"))

        problems = validate(rows, md)
        validated = not problems and not note

        for r in rows:
            key = slug(r.get("name") or r.get("level") or r.get("condition")
                       or r.get("category") or r.get("item") or r.get("raw", ""))
            by_family.setdefault(family, {})[key] = {
                "_page": page, "_validated": validated, **r}

        if problems or note:
            review.append({"page": page, "family": family,
                           "problems": problems[:8], "note": note, "raw": md[:300]})

        if (ti + 1) % 25 == 0:
            print(f"{ti + 1}/{len(tables)}", flush=True)

    ss = extract_skill_stats()
    by_family["skills_stat"] = {k: {"_page": v["_page"], "_validated": True, **v}
                                for k, v in ss.items()}
    print(f"skills_stat (regex): {len(ss)}")

    for family, rows in by_family.items():
        with open(OUT / f"{family}.jsonl", "w", encoding="utf-8") as f:
            for key, rec in rows.items():
                f.write(json.dumps({"key": key, **rec}, ensure_ascii=False) + "\n")
        print(f"{family}: {len(rows)} rows")

    with open(REVIEW, "w", encoding="utf-8") as f:
        for r in review:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"review queue: {len(review)}")


if __name__ == "__main__":
    main()