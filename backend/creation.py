"""Создание персонажа. Все пулы, списки и лимиты берутся из data/rules (книга).
Пресеты ролей остаются как ЯВНЫЕ домашние шаблоны для быстрого теста."""
import random

from backend import rules

ROLE_ALIASES = {
    "techie": "Tech", "tech": "Tech", "netrunner": "Netrunner", "solo": "Solo",
    "rockerboy": "Rockerboy", "fixer": "Fixer", "nomad": "Nomad",
    "medtech": "Medtech", "lawman": "Lawman", "exec": "Exec", "media": "Media",
}

# Домашние значения по умолчанию: используются ТОЛЬКО пока книга не подтверждена,
# и всегда помечаются в options() как house.
HOUSE = {
    "roles": ["Solo", "Netrunner", "Tech", "Rockerboy", "Fixer", "Nomad",
              "Medtech", "Lawman", "Exec", "Media"],
    "stat_list": ["INT", "REF", "DEX", "TECH", "COOL", "WILL", "LUCK", "MOVE", "BODY", "EMP"],
    "stat_min": 2, "stat_max": 8,
    "stat_pool_edgerunner": 60, "skill_pool_edgerunner": 30, "skill_max_at_creation": 6,
    "skill_list": [
        {"key": "handgun", "stat": "REF"}, {"key": "melee_weapon", "stat": "DEX"},
        {"key": "martial_arts", "stat": "DEX"}, {"key": "evasion", "stat": "DEX"},
        {"key": "athletics", "stat": "DEX"}, {"key": "perception", "stat": "INT"},
        {"key": "stealth", "stat": "DEX"}, {"key": "persuasion", "stat": "COOL"},
        {"key": "conversation", "stat": "EMP"}, {"key": "intimidation", "stat": "COOL"},
        {"key": "trading", "stat": "COOL"}, {"key": "interface", "stat": "INT"},
        {"key": "programming", "stat": "INT"},
        {"key": "electronics_security_tech", "stat": "TECH"},
        {"key": "basic_tech", "stat": "TECH"}, {"key": "weaponstech", "stat": "TECH"},
        {"key": "drive_land_vehicle", "stat": "REF"}, {"key": "first_aid", "stat": "TECH"},
        {"key": "streetwise", "stat": "COOL"}, {"key": "deduction", "stat": "INT"},
    ],
    "gear": ["agent", "cyberdeck", "toolkit", "medkit", "flashlight", "lockpick",
             "grapple", "camera", "armored_jacket", "restraints"],
    "weapons": ["heavy_pistol", "medium_pistol", "knife", "baton",
                "assault_rifle", "shotgun", "sniper_rifle"],
    "armors": ["leathers", "light_armorjack", "medium_armorjack", "heavy_armorjack", "kevlar"],
    "programs": ["sword", "armor", "shield", "banhammer", "deckkrash",
                 "hellhound", "seeya", "pathfinder"],
    "gear_limit": 4, "prog_limit": 3, "starting_eb": 1000,
}

HANDLES = ["Вектор", "Никс", "Ржавчина", "Спектр", "Кобальт", "Шрам", "Люмен", "Гризли"]

ROLE_PRESETS = {
    "Solo":      {"stats": {"INT": 3, "REF": 7, "DEX": 5, "TECH": 3, "COOL": 5, "WILL": 4, "LUCK": 2, "MOVE": 5, "BODY": 6, "EMP": 3},
                  "skills": {"handgun": 4, "melee_weapon": 3, "evasion": 3, "athletics": 3, "perception": 3},
                  "weapon": "heavy_pistol", "armor": "light_armorjack",
                  "gear": ["armored_jacket", "knife"], "cyber": ["Neural Link"], "programs": []},
    "Netrunner": {"stats": {"INT": 6, "REF": 4, "DEX": 3, "TECH": 5, "COOL": 4, "WILL": 4, "LUCK": 3, "MOVE": 4, "BODY": 4, "EMP": 4},
                  "skills": {"interface": 4, "programming": 3, "stealth": 3, "perception": 2, "electronics_security_tech": 2},
                  "weapon": "medium_pistol", "armor": "leathers",
                  "gear": ["cyberdeck", "agent"], "cyber": ["Neural Link", "Interface Plugs"],
                  "programs": ["sword", "armor", "seeya"]},
    "Tech":      {"stats": {"INT": 5, "REF": 4, "DEX": 4, "TECH": 7, "COOL": 4, "WILL": 4, "LUCK": 3, "MOVE": 4, "BODY": 4, "EMP": 4},
                  "skills": {"basic_tech": 4, "weaponstech": 3, "electronics_security_tech": 3, "perception": 2},
                  "weapon": "medium_pistol", "armor": "leathers",
                  "gear": ["toolkit", "lockpick"], "cyber": ["Neural Link"], "programs": []},
}
_DEFAULT = {"stats": {"INT": 4, "REF": 4, "DEX": 4, "TECH": 4, "COOL": 5, "WILL": 4, "LUCK": 3, "MOVE": 4, "BODY": 4, "EMP": 4},
            "skills": {"persuasion": 3, "conversation": 3, "perception": 2, "streetwise": 2},
            "weapon": "medium_pistol", "armor": "leathers",
            "gear": ["agent"], "cyber": ["Neural Link"], "programs": []}


def _book(key, pack="creation"):
    """Значение из книги либо явный house-fallback."""
    return rules.get(pack, key, house=HOUSE.get(key))


def _sources(keys):
    return {k: rules.provenance("creation", k) for k in keys}


def limits():
    return {
        "stat_min": int(_book("stat_min")), "stat_max": int(_book("stat_max")),
        "stat_pool": int(_book("stat_pool_edgerunner")),
        "skill_pool": int(_book("skill_pool_edgerunner")),
        "skill_max": int(_book("skill_max_at_creation")),
        "gear_limit": int(HOUSE["gear_limit"]), "prog_limit": int(HOUSE["prog_limit"]),
    }


def normalize_role(role):
    roles = _book("roles")
    if not role:
        return random.choice(roles)
    r = ROLE_ALIASES.get(str(role).strip().lower(), "Solo")
    return r if r in roles else roles[0]


def preset(role):
    r = normalize_role(role)
    return ROLE_PRESETS.get(r, _DEFAULT), r


def _finalize(name, role, stats, skills, weapon, armor, gear, cyber, programs):
    from backend import rules_tables
    emp = stats.get("EMP", 4)
    hp = int(rules_tables.max_hp(stats))
    return {
        "name": name, "role": role, "stats": dict(stats), "skills": dict(skills),
        "hp": hp, "max_hp": hp, "wound": "unharmed", "dsp": 0, "dead": False,
        "armor": armor, "weapon": weapon, "eb": int(_book("starting_eb")),
        "humanity": emp * 10, "cyberware": list(cyber),
        "inventory": list(dict.fromkeys([weapon, armor] + gear)),
        "programs": list(programs), "active_effects": [],
        "rules_provenance": {
            "hp_formula": rules.provenance("creation", "hp_formula"),
            "sources": _sources(["stat_pool_edgerunner", "skill_pool_edgerunner"]),
        },
    }


def random_character(role=None, name=None):
    p, r = preset(role)
    return _finalize(name or random.choice(HANDLES), r, p["stats"], p["skills"],
                     p["weapon"], p["armor"], p["gear"], p["cyber"], p["programs"])


def options(role=None):
    p, r = preset(role)
    lim = limits()
    skill_list = _book("skill_list")
    return {
        "role": r, "roles": _book("roles"),
        "stats": _book("stat_list"),
        "stat_min": lim["stat_min"], "stat_max": lim["stat_max"], "stat_pool": lim["stat_pool"],
        "skills": [s["key"] if isinstance(s, dict) else s for s in skill_list],
        "skill_stat": {s["key"]: s["stat"] for s in skill_list if isinstance(s, dict)},
        "skill_pool": lim["skill_pool"], "skill_max": lim["skill_max"],
        "gear": _book("gear"), "gear_limit": lim["gear_limit"],
        "weapons": _book("weapons"), "armors": _book("armors"),
        "programs": _book("programs"), "prog_limit": lim["prog_limit"],
        "preset": p,
        "sources": _sources(["roles", "stat_list", "stat_min", "stat_max",
                             "stat_pool_edgerunner", "skill_pool_edgerunner",
                             "skill_max_at_creation", "skill_list", "starting_eb"]),
        "house_keys": sorted(k for k, v in rules.house_hits().items() if v is not None),
    }


def build(spec):
    lim = limits()
    role = normalize_role(spec.get("role"))
    stat_keys = _book("stat_list")
    stats = {k: int(spec.get("stats", {}).get(k, lim["stat_min"])) for k in stat_keys}
    if any(not (lim["stat_min"] <= v <= lim["stat_max"]) for v in stats.values()):
        raise ValueError(f"статы вне диапазона {lim['stat_min']}..{lim['stat_max']}")
    if sum(stats.values()) > lim["stat_pool"]:
        raise ValueError(f"пул статов превышен (макс {lim['stat_pool']})")
    allowed = {s["key"] if isinstance(s, dict) else s for s in _book("skill_list")}
    skills = {k: int(v) for k, v in (spec.get("skills") or {}).items()
              if int(v) > 0 and k in allowed}
    if any(v > lim["skill_max"] for v in skills.values()):
        raise ValueError(f"навык выше лимита создания {lim['skill_max']}")
    if sum(skills.values()) > lim["skill_pool"]:
        raise ValueError(f"пул навыков превышен (макс {lim['skill_pool']})")
    gear = [g for g in (spec.get("gear") or []) if g in _book("gear")][:lim["gear_limit"]]
    weapon = spec.get("weapon") if spec.get("weapon") in _book("weapons") else "medium_pistol"
    armor = spec.get("armor") if spec.get("armor") in _book("armors") else "leathers"
    programs = [p for p in (spec.get("programs") or []) if p in _book("programs")][:lim["prog_limit"]]
    cyber = ["Neural Link"]
    if role == "Netrunner":
        cyber.append("Interface Plugs")
        if "cyberdeck" not in gear:
            gear.append("cyberdeck")
    return _finalize(spec.get("name") or random.choice(HANDLES), role, stats, skills,
                     weapon, armor, gear, cyber, programs)