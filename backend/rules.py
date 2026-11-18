"""Единый источник истины по правилам Cyberpunk RED.

Значения живут в data/rules/<pack>.json и извлекаются из Core Rulebook.
Каждая запись хранит provenance: страница, идентификатор чанка, флаг verified.
Непроверенное значение НЕ используется молча: либо явный house-rule,
либо исключение UnverifiedRule.
"""
import datetime
import json
import pathlib
import threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
RULES_DIR = ROOT / "data" / "rules"
BOOK = "Cyberpunk RED Core Rulebook"

_LOCK = threading.RLock()          # реентерабельный: put -> load больше не клинит
_CACHE = {}
_HOUSE_HITS = {}


class UnverifiedRule(KeyError):
    """Значение не подтверждено по книге и для него не задан house-rule."""


def _path(pack):
    return RULES_DIR / f"{pack}.json"


def _load_unlocked(pack, force=False):
    if force or pack not in _CACHE:
        p = _path(pack)
        if p.exists():
            _CACHE[pack] = json.loads(p.read_text(encoding="utf-8"))
        else:
            _CACHE[pack] = {"pack": pack, "book": BOOK, "entries": {}}
    return _CACHE[pack]


def _write_unlocked(pack, data):
    RULES_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _path(pack).with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(_path(pack))
    _CACHE[pack] = data


def _record(value, page, chunk, note, verified):
    return {"value": value, "page": page, "chunk": chunk,
            "verified": bool(verified), "note": note,
            "updated": datetime.datetime.now(datetime.timezone.utc).isoformat()}


def load(pack, force=False):
    with _LOCK:
        return _load_unlocked(pack, force)


def entry(pack, key):
    return load(pack)["entries"].get(key)


def provenance(pack, key):
    e = entry(pack, key) or {}
    return {"page": e.get("page"), "chunk": e.get("chunk"),
            "verified": bool(e.get("verified")), "note": e.get("note", "")}


def get(pack, key, house=None):
    e = entry(pack, key)
    if e and e.get("verified") and e.get("value") is not None:
        return e["value"]
    if house is not None:
        _HOUSE_HITS[f"{pack}.{key}"] = house
        return house
    raise UnverifiedRule(f"{pack}.{key}: нет подтверждённого значения по книге")


def num(pack, key, house=None):
    return int(get(pack, key, house))

def get_optional(pack, key, default=None):
    """Значение из книги, если подтверждено; иначе default. Никогда не бросает."""
    e = entry(pack, key)
    if e and e.get("verified") and e.get("value") is not None:
        return e["value"]
    return default

def put(pack, key, value, page=None, chunk=None, note="", verified=True):
    with _LOCK:
        data = _load_unlocked(pack)
        data["entries"][key] = _record(value, page, chunk, note, verified)
        _write_unlocked(pack, data)
        return data["entries"][key]


def put_many(pack, items):
    """Пакетная запись: один файл-райт на весь список."""
    with _LOCK:
        data = _load_unlocked(pack)
        for it in items:
            data["entries"][it["key"]] = _record(
                it.get("value"), it.get("page"), it.get("chunk"),
                it.get("note", ""), it.get("verified", False))
        _write_unlocked(pack, data)
        return len(items)


def skeleton(pack, keys, note="ожидает извлечения из книги"):
    """Добавляет только отсутствующие ключи, одним файлом-райтом."""
    with _LOCK:
        data = _load_unlocked(pack)
        added = [k for k in keys if k not in data["entries"]]
        for k in added:
            data["entries"][k] = _record(None, None, None, note, False)
        if added:
            _write_unlocked(pack, data)
        return added


def house_hits():
    return dict(_HOUSE_HITS)


def status():
    packs = {}
    if RULES_DIR.exists():
        for p in sorted(RULES_DIR.glob("*.json")):
            d = json.loads(p.read_text(encoding="utf-8"))
            ents = d.get("entries", {})
            packs[d.get("pack", p.stem)] = {
                "total": len(ents),
                "verified": sum(1 for e in ents.values() if e.get("verified")),
                "unverified": sum(1 for e in ents.values() if not e.get("verified")),
            }
    return {"book": BOOK, "packs": packs, "house_hits": house_hits()}
 
def verified(pack, key):
    e = entry(pack, key)
    return bool(e and e.get("verified"))


def value_or(pack, key, default=None):
    """Возвращает книжное значение, включая ЯВНЫЙ null (в книге пула нет)."""
    e = entry(pack, key)
    if e and e.get("verified"):
        return e.get("value")
    return default 