"""Полноценное создание персонажа: point-buy статы, навыки, снаряжение, программы.
Не зависит от chargen.py; используется и быстрым /chargen, и полным билдером онлайна."""
import random

ROLE_ALIASES = {
    "techie": "Tech", "tech": "Tech", "netrunner": "Netrunner", "solo": "Solo",
    "rockerboy": "Rockerboy", "fixer": "Fixer", "nomad": "Nomad",
    "medtech": "Medtech", "lawman": "Lawman", "exec": "Exec", "media": "Media",
}
ROLES = ["Solo", "Netrunner", "Tech", "Rockerboy", "Fixer", "Nomad",
         "Medtech", "Lawman", "Exec", "Media"]

STATS = ["INT", "REF", "DEX", "TECH", "COOL", "WILL", "LUCK", "MOVE", "BODY", "EMP"]
STAT_POOL, STAT_MIN, STAT_MAX = 60, 2, 8
SKILL_POOL, SKILL_MAX = 30, 6
SKILLS = ["handgun", "melee_weapon", "martial_arts", "evasion", "athletics",
          "perception", "stealth", "persuasion", "conversation", "intimidation",
          "trading", "interface", "programming", "electronics_security_tech",
          "basic_tech", "weaponstech", "drive_land_vehicle", "first_aid",
          "streetwise", "deduction"]
GEAR = ["agent", "cyberdeck", "toolkit", "medkit", "flashlight", "lockpick",
        "grapple", "camera", "armored_jacket", "restraints"]
WEAPON_CHOICES = ["heavy_pistol", "medium_pistol", "knife", "baton",
                  "assault_rifle", "shotgun", "sniper_rifle"]
ARMOR_CHOICES = ["leathers", "light_armorjack", "medium_armorjack",
                 "heavy_armorjack", "kevlar"]
PROGRAMS = ["sword", "armor", "shield", "banhammer", "deckkrash",
            "hellhound", "seeya", "pathfinder"]
GEAR_LIMIT, PROG_LIMIT = 4, 3

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


def normalize_role(role):
    if not role:
        return random.choice(ROLES)
    return ROLE_ALIASES.get(str(role).strip().lower(), "Solo")


def preset(role):
    r = normalize_role(role)
    return ROLE_PRESETS.get(r, _DEFAULT), r


def _finalize(name, role, stats, skills, weapon, armor, gear, cyber, programs):
    body, will, emp = stats.get("BODY", 4), stats.get("WILL", 4), stats.get("EMP", 4)
    hp = body + will + 2
    return {
        "name": name, "role": role, "stats": dict(stats), "skills": dict(skills),
        "hp": hp, "max_hp": hp, "wound": "unharmed", "dsp": 0, "dead": False,
        "armor": armor, "weapon": weapon, "eb": 1000, "humanity": emp * 10,
        "cyberware": list(cyber), "inventory": list(dict.fromkeys([weapon, armor] + gear)),
        "programs": list(programs), "active_effects": [],
    }


def random_character(role=None, name=None):
    p, r = preset(role)
    return _finalize(name or random.choice(HANDLES), r, p["stats"], p["skills"],
                     p["weapon"], p["armor"], p["gear"], p["cyber"], p["programs"])


def options(role=None):
    p, r = preset(role)
    return {"role": r, "roles": ROLES, "stats": STATS, "stat_pool": STAT_POOL,
            "stat_min": STAT_MIN, "stat_max": STAT_MAX, "skills": SKILLS,
            "skill_pool": SKILL_POOL, "skill_max": SKILL_MAX, "gear": GEAR,
            "gear_limit": GEAR_LIMIT, "weapons": WEAPON_CHOICES, "armors": ARMOR_CHOICES,
            "programs": PROGRAMS, "prog_limit": PROG_LIMIT, "preset": p}


def build(spec):
    role = normalize_role(spec.get("role"))
    stats = {k: int(spec.get("stats", {}).get(k, STAT_MIN)) for k in STATS}
    if any(not (STAT_MIN <= v <= STAT_MAX) for v in stats.values()):
        raise ValueError("статы вне диапазона 2..8")
    if sum(stats.values()) > STAT_POOL:
        raise ValueError(f"пул статов превышен (макс {STAT_POOL})")
    skills = {k: int(v) for k, v in (spec.get("skills") or {}).items() if int(v) > 0}
    if any(not (0 <= v <= SKILL_MAX) for v in skills.values()):
        raise ValueError("навык вне диапазона 0..6")
    if sum(skills.values()) > SKILL_POOL:
        raise ValueError(f"пул навыков превышен (макс {SKILL_POOL})")
    gear = [g for g in (spec.get("gear") or []) if g in GEAR][:GEAR_LIMIT]
    weapon = spec.get("weapon") if spec.get("weapon") in WEAPON_CHOICES else "medium_pistol"
    armor = spec.get("armor") if spec.get("armor") in ARMOR_CHOICES else "leathers"
    programs = [p for p in (spec.get("programs") or []) if p in PROGRAMS][:PROG_LIMIT]
    cyber = ["Neural Link"]
    if role == "Netrunner":
        cyber.append("Interface Plugs")
        if "cyberdeck" not in gear:
            gear.append("cyberdeck")
    return _finalize(spec.get("name") or random.choice(HANDLES), role, stats, skills,
                     weapon, armor, gear, cyber, programs)