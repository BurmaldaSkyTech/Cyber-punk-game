"""Слияние книжных таблиц с базовыми таблицами движка и формула HP из книги."""
import math
import re

from backend import rules
from tools.rules_normalize import MELEE_MAP


def dv_table(base):
    out = dict(base)
    book = rules.get_optional("combat", "dv_table")
    if isinstance(book, dict):
        out.update({k: int(v) for k, v in book.items()})
    return out


def armor_table(base):
    out = {k: dict(v) for k, v in base.items()}
    book = rules.get_optional("armor", "table")
    if isinstance(book, dict):
        for k, v in book.items():
            cur = out.setdefault(k, {})
            if v.get("is_shield"):
                cur["is_shield"] = True
                if v.get("hp") is not None:
                    cur["hp"] = v["hp"]
                if v.get("price") is not None:
                    cur["price"] = v["price"]
                continue
            if "sp" in v:
                cur["sp"] = v["sp"]
            pen = v.get("penalty") or {}
            cur["penalty"] = pen.get("value", 0)
            cur["penalty_stats"] = pen.get("stats", [])
            if v.get("price") is not None:
                cur["price"] = v["price"]
        if "metalgear" in out and "bodyplate" in out:
            out["bodyplate"].update(out["metalgear"])
            out["bodyplate"]["book_alias"] = "metalgear"
    return out


def weapon_table(base):
    out = {k: dict(v) for k, v in base.items()}
    book = rules.get_optional("weapons", "table")
    if not isinstance(book, dict):
        return out
    for k, v in book.items():
        if v.get("category"):
            continue
        if k in out:
            out[k].update({f: val for f, val in v.items() if f != "name"})
    for engine_key, cat in MELEE_MAP.items():
        if engine_key in out and cat in book:
            c = book[cat]
            out[engine_key]["damage"] = c.get("damage", out[engine_key].get("damage"))
            out[engine_key]["rof"] = c.get("rof", out[engine_key].get("rof", 2))
            out[engine_key]["skill"] = "melee_weapon"
            out[engine_key]["book_category"] = cat
    return out


def max_hp(stats):
    """HP по книжной формуле; иначе явно домашний масштаб."""
    body = int(stats.get("BODY", 4))
    will = int(stats.get("WILL", 4))
    f = rules.get_optional("creation", "hp_formula")
    if isinstance(f, str):
        s = f.lower()
        m_base = re.search(r"(\d+)\s*\+", s)
        m_mult = re.search(r"(\d+)\s*[×x*]", s)
        if m_base and m_mult and ("average" in s or "averaged" in s):
            base, mult = int(m_base.group(1)), int(m_mult.group(1))
            avg = math.ceil((body + will) / 2)
            if "rounding up" in s or "round up" in s or "↑" in s:
                avg = math.ceil((body + will) / 2)
            return base + mult * avg
    return body + will + 2