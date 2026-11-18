# Каталог создания персонажа: пакеты ролей, магазин, боевые искусства.
# Цены оружия/брони — из книги (data/rules); остальное — house до извлечения.
import random
from backend import engine, rules

ROLES = ["Solo", "Netrunner", "Tech", "Rockerboy", "Fixer", "Nomad", "Medtech", "Lawman", "Exec", "Media"]

ROLE_TEMPLATES = {
    "Solo": {"stats": {"INT": 3, "REF": 7, "DEX": 5, "TECH": 3, "COOL": 5, "WILL": 4, "LUCK": 2, "MOVE": 5, "BODY": 6, "EMP": 3}, "skills": {"handgun": 4, "melee_weapon": 3, "evasion": 3, "athletics": 3, "perception": 3}, "weapon": "heavy_pistol", "armor": "light_armorjack", "gear": ["armored_jacket", "knife"], "cyber": ["Neural Link"], "programs": []},
    "Netrunner": {"stats": {"INT": 6, "REF": 4, "DEX": 3, "TECH": 5, "COOL": 4, "WILL": 4, "LUCK": 3, "MOVE": 4, "BODY": 4, "EMP": 4}, "skills": {"interface": 4, "programming": 3, "stealth": 3, "perception": 2, "electronics_security_tech": 2}, "weapon": "medium_pistol", "armor": "leathers", "gear": ["cyberdeck", "agent"], "cyber": ["Neural Link", "Interface Plugs"], "programs": ["sword", "armor", "seeya"]},
    "Tech": {"stats": {"INT": 5, "REF": 4, "DEX": 4, "TECH": 7, "COOL": 4, "WILL": 4, "LUCK": 3, "MOVE": 4, "BODY": 4, "EMP": 4}, "skills": {"basic_tech": 4, "weaponstech": 3, "electronics_security_tech": 3, "perception": 2}, "weapon": "medium_pistol", "armor": "leathers", "gear": ["toolkit", "lockpick"], "cyber": ["Neural Link"], "programs": []},
}
DEFAULT_TEMPLATE = {"stats": {"INT": 4, "REF": 4, "DEX": 4, "TECH": 4, "COOL": 5, "WILL": 4, "LUCK": 3, "MOVE": 4, "BODY": 4, "EMP": 4}, "skills": {"persuasion": 3, "conversation": 3, "perception": 2, "streetwise": 2}, "weapon": "medium_pistol", "armor": "leathers", "gear": ["agent"], "cyber": ["Neural Link"], "programs": []}

HOUSE_STARTING_EB = {"streetrat": 0, "edgerunner": 1000, "complete_package": 1000}
HOUSE_GEAR = {"agent": 100, "cyberdeck": 500, "toolkit": 100, "medkit": 50, "flashlight": 20, "lockpick": 50, "grapple": 100, "camera": 100, "armored_jacket": 100, "restraints": 20, "antidote": 100}
HOUSE_CYBER = {"Neural Link": {"price": 500, "hl": 0}, "Interface Plugs": {"price": 500, "hl": 2}, "Basic Cyberoptic": {"price": 500, "hl": 2}, "Cyberaudio Suite": {"price": 500, "hl": 2}, "Wolvers": {"price": 500, "hl": 3}, "Subdermal Armor": {"price": 1000, "hl": 3}, "Kerenzikov": {"price": 1000, "hl": 4}, "Sandevistan": {"price": 1000, "hl": 4}}
HOUSE_DRUGS = {"speedheal": 100, "blacklace": 200, "syncomp": 150, "boost": 100, "dorph": 250, "smash": 50}
HOUSE_PROGRAMS = {"sword": 100, "armor": 100, "shield": 100, "banhammer": 250, "deckkrash": 500, "hellhound": 500, "seeya": 100, "pathfinder": 250}
HOUSE_WEAPON_PRICE = {"knife": 50, "bat": 50, "machete": 100, "axe": 100, "chainsaw": 500, "grenade": 100, "baton": 50}
MARTIAL_FORMS = ["Aikido", "Animal Kung Fu", "Boxing", "Capoeira", "Choi Li Fut", "Judo", "Karate", "Taekwondo", "Thai Kick Boxing", "Wrestling"]
HOUSE_MOVE_LEVELS = {"sweep": 1, "disarm": 3, "throw": 5}


def template(role):
    return ROLE_TEMPLATES.get(role, DEFAULT_TEMPLATE)


def skill_master():
    book = rules.get_optional("creation", "skill_list")
    if isinstance(book, list) and book:
        return {s["key"]: s["stat"] for s in book if isinstance(s, dict) and s.get("key")}
    if isinstance(book, dict) and book:
        return dict(book)
    return dict(engine.SKILL_STAT)


def starting_eb(method):
    v = rules.get_optional("creation", "starting_eb_" + str(method))
    if isinstance(v, (int, float)):
        return int(v), "book"
    return int(HOUSE_STARTING_EB.get(method, 1000)), "house"


def _item(key, name, category, price, source, **meta):
    d = {"key": key, "name": name, "category": category, "price": int(price), "source": source}
    d.update(meta)
    return d


def catalog():
    items = []
    for k, w in engine.WEAPONS.items():
        p = w.get("price")
        items.append(_item(k, w.get("name", k), "weapon",
                           p if p is not None else HOUSE_WEAPON_PRICE.get(k, 100),
                           "book" if p is not None else "house",
                           damage=w.get("damage"), rof=w.get("rof"), skill=w.get("skill")))
    for k, a in engine.ARMOR.items():
        if a.get("house_item"):
            continue
        p = a.get("price")
        items.append(_item(k, k, "armor", p if p is not None else 100,
                           "book" if p is not None else "house",
                           sp=a.get("sp"), penalty=a.get("penalty", 0)))
    for k, p in HOUSE_GEAR.items():
        items.append(_item(k, k, "gear", p, "house"))
    for k, v in HOUSE_CYBER.items():
        items.append(_item(k, k, "cyberware", v["price"], "house", hl=v["hl"]))
    for k, p in HOUSE_DRUGS.items():
        items.append(_item(k, k, "drug", p, "house"))
    for k, p in HOUSE_PROGRAMS.items():
        items.append(_item(k, k, "program", p, "house"))
    return items


def martial_options(level):
    lvl = int(level or 0)
    bf = rules.get_optional("combat", "martial_arts_forms")
    forms = bf if isinstance(bf, list) and bf else MARTIAL_FORMS
    moves = [{"key": k, "min_level": v} for k, v in HOUSE_MOVE_LEVELS.items() if lvl >= v]
    return {"required": lvl >= 1, "forms": forms, "moves": moves,
            "source": "book" if isinstance(bf, list) and bf else "house"}


def roll_stats():
    lo = int(rules.get("creation", "stat_min", house=2))
    hi = int(rules.get("creation", "stat_max", house=8))
    keys = rules.get("creation", "stat_list",
                     house=["INT", "REF", "DEX", "TECH", "COOL", "WILL", "LUCK", "MOVE", "BODY", "EMP"])
    return {k: max(lo, min(hi, random.randint(1, 10))) for k in keys}
