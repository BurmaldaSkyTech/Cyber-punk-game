"""Нормализация «книжных» имён и единиц в ключи движка."""
import re

MELEE_MAP = {
    "knife": "light_melee_weapon", "combat_knife": "light_melee_weapon",
    "tomahawk": "light_melee_weapon",
    "bat": "medium_melee_weapon", "baton": "medium_melee_weapon",
    "machete": "medium_melee_weapon", "crowbar": "medium_melee_weapon",
    "axe": "heavy_melee_weapon", "sword": "heavy_melee_weapon",
    "lead_pipe": "heavy_melee_weapon", "spiked_bat": "heavy_melee_weapon",
    "chainsaw": "very_heavy_melee_weapon", "sledgehammer": "very_heavy_melee_weapon",
}


def clean(s):
    return re.sub(r"\s+", " ", s).strip() if isinstance(s, str) else s


def snake(s):
    s = clean(s).replace("®", "").replace("™", "")
    return re.sub(r"[^0-9A-Za-z]+", "_", s).strip("_").lower()


def parse_eb(v):
    digits = re.sub(r"[^0-9]", "", str(v))
    return int(digits) if digits else None


def parse_penalty(v):
    if v is None:
        return {"value": 0, "stats": []}
    if isinstance(v, (int, float)):
        return {"value": int(v), "stats": ["REF", "DEX", "MOVE"]}
    s = clean(v)
    if s.lower() in ("none", "-", "—", ""):
        return {"value": 0, "stats": []}
    m = re.search(r"(-?\d+)", s)
    stats = [x for x in ("REF", "DEX", "MOVE") if x in s.upper()]
    return {"value": int(m.group(1)) if m else 0,
            "stats": stats or ["REF", "DEX", "MOVE"]}


def norm_dv(raw):
    return {snake(k): int(v) for k, v in raw.items()}


def norm_armor(raw):
    out = {}
    for name, rec in raw.items():
        r = {snake(k): clean(v) for k, v in rec.items()}
        e = {"name": clean(name)}
        if "sp" in r:
            e["sp"] = int(r["sp"])
        if "hp" in r:
            e["hp"] = int(r["hp"])
            e["is_shield"] = True
        e["penalty"] = parse_penalty(r.get("penalty"))
        price = r.get("cost", r.get("price"))
        if price is not None:
            e["price"] = parse_eb(price)
        out[snake(name)] = e
    return out


def norm_weapons(raw):
    out = {}
    for name, rec in raw.items():
        r = {snake(k): clean(v) for k, v in rec.items()}
        e = {"name": clean(name)}
        if "damage" in r:
            e["damage"] = str(r["damage"]).replace(" ", "")
        if "rof" in r:
            e["rof"] = int(r["rof"])
        if "mag" in r:
            e["mag"] = int(r["mag"])
        if "skill" in r:
            e["skill"] = snake(r["skill"])
        if "conceal" in r:
            e["conceal"] = str(r["conceal"]).upper().startswith("Y")
        price = r.get("price", r.get("cost"))
        if price is not None:
            e["price"] = parse_eb(price)
        if "examples" in r:
            e["examples"] = [clean(x) for x in str(r["examples"]).split(",")]
            e["category"] = True
            e.setdefault("skill", "melee_weapon")
        out[snake(name)] = e
    return out


NORMALIZERS = {"dv_table": norm_dv, "table_armor": norm_armor, "table_weapons": norm_weapons}


def normalize_entry(pack, key, value):
    if pack == "combat" and key == "dv_table" and isinstance(value, dict):
        return norm_dv(value)
    if pack == "armor" and key == "table" and isinstance(value, dict):
        return norm_armor(value)
    if pack == "weapons" and key == "table" and isinstance(value, dict):
        return norm_weapons(value)
    return value