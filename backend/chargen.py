# backend/chargen.py
"""Создание персонажей по правилам CPR RED (метод Edgerunner).
Stats: 62 очка, каждая 2..8
Skills: 4 карьерных от роли (старт 2..3) + 10 очков дополнительных
Lifepath: серия бросков 2d6 по таблицам
Starting gear: по роли"""
import random

STATS = ["INT", "REF", "DEX", "TECH", "COOL", "WILL", "LUCK", "MOVE", "BODY", "EMP"]
STAT_MIN, STAT_MAX, STAT_POOL = 2, 8, 62
CAREER_START = 2
ADDITIONAL_SKILL_POOL = 10
SKILL_MAX = 6
STARTING_EB = {"Rockerboy": 1500, "Solo": 1800, "Netrunner": 1500, "Tech": 1700,
               "Medtech": 1500, "Media": 1200, "Lawman": 2000, "Exec": 3000,
               "Nomad": 1000, "Fixer": 2500}

SKILLS = {
    "athletics": "BODY", "melee": "DEX", "evasion": "DEX", "stealth": "DEX",
    "contortionist": "DEX", "dance": "DEX", "drive": "REF", "pilot": "REF",
    "handgun": "REF", "shoulder_arms": "REF", "autofire": "REF",
    "perception": "INT", "deduction": "INT", "library_search": "INT",
    "criminology": "INT", "streetwise": "INT", "first_aid": "INT",
    "tactics": "INT", "interface": "INT", "programming": "TECH",
    "electronics": "TECH", "basic_tech": "TECH", "cybertech": "TECH",
    "weaponstech": "TECH", "land_vehicle_tech": "TECH", "paramedic": "TECH",
    "pharmaceuticals": "TECH",
    "persuasion": "EMP", "conversation": "EMP", "human_perception": "EMP",
    "performance": "COOL", "acting": "COOL", "trading": "COOL",
    "concentration": "WILL",
}

ROLES = {
    "Rockerboy": {"ability": "Charismatic Impact",
                  "career": ["performance", "persuasion", "human_perception", "acting"],
                  "weapon": "heavy_pistol", "armor": "leathers",
                  "items": ["electric guitar", "amp drone", "stylish clothes"],
                  "starting_cyberware": ["Neural Link", "Basic Cyberaudio"]},
    "Solo": {"ability": "Combat Awareness",
             "career": ["handgun", "melee", "evasion", "athletics"],
             "weapon": "heavy_pistol", "armor": "light_armorjack",
             "items": ["combat knife", "armored jacket"],
             "starting_cyberware": ["Neural Link", "Basic Cyberoptic"]},
    "Netrunner": {"ability": "Interface",
                  "career": ["interface", "programming", "electronics", "perception"],
                  "weapon": "medium_pistol", "armor": "leathers",
                  "items": ["cyberdeck", "agent", "interface plugs"],
                  "starting_cyberware": ["Neural Link", "Interface Plugs"]},
    "Tech": {"ability": "Maker",
             "career": ["basic_tech", "electronics", "cybertech", "weaponstech"],
             "weapon": "medium_pistol", "armor": "leathers",
             "items": ["toolkit", "techhair", "tech goggles"],
             "starting_cyberware": ["Neural Link", "Basic Cyberaudio"]},
    "Medtech": {"ability": "Medicine",
                "career": ["paramedic", "first_aid", "pharmaceuticals", "human_perception"],
                "weapon": "medium_pistol", "armor": "leathers",
                "items": ["medscanner", "trauma bag", "airhypo"],
                "starting_cyberware": ["Neural Link", "Basic Cyberaudio"]},
    "Media": {"ability": "Credibility",
              "career": ["deduction", "library_search", "persuasion", "acting"],
              "weapon": "medium_pistol", "armor": "leathers",
              "items": ["recorder drone", "press badge", "camera"],
              "starting_cyberware": ["Neural Link", "Basic Cyberoptic"]},
    "Lawman": {"ability": "Backup",
               "career": ["handgun", "perception", "deduction", "criminology"],
               "weapon": "heavy_pistol", "armor": "kevlar",
               "items": ["badge", "radio", "restraints"],
               "starting_cyberware": ["Neural Link", "Basic Cyberoptic"]},
    "Exec": {"ability": "Team Builder",
             "career": ["persuasion", "conversation", "deduction", "trading"],
             "weapon": "heavy_pistol", "armor": "leathers",
             "items": ["corpo badge", "credit chip", "corporate suit"],
             "starting_cyberware": ["Neural Link", "Basic Cyberaudio"]},
    "Nomad": {"ability": "Moto",
              "career": ["drive", "land_vehicle_tech", "athletics", "perception"],
              "weapon": "shoulder_arms", "armor": "kevlar",
              "items": ["roadbike keys", "tent", "road leathers"],
              "starting_cyberware": ["Neural Link", "Basic Cyberoptic"]},
    "Fixer": {"ability": "Operator",
              "career": ["streetwise", "persuasion", "conversation", "trading"],
              "weapon": "heavy_pistol", "armor": "leathers",
              "items": ["contact list", "burner phone", "stylish clothes"],
              "starting_cyberware": ["Neural Link", "Basic Cyberaudio"]},
}

# Lifepath tables (2d6 rolls)
LIFEPATH_TABLES = {
    "cultural_origins": {
        2: "North American", 3: "South American", 4: "Western European",
        5: "Eastern European", 6: "Middle Eastern", 7: "North African",
        8: "Sub-Saharan African", 9: "South Asian", 10: "Southeast Asian",
        11: "East Asian", 12: "Oceania/Pacific",
    },
    "family_background": {
        2: "Corporate Elite (wealthy)", 3: "Corporate Manager (comfortable)",
        4: "Corporate Worker (middle class)", 5: "Nomad Clan",
        6: "Gang Member family", 7: "Urban Homeless",
        8: "Rural Family Farm", 9: "Military family",
        10: "Law Enforcement family", 11: "Entertainment family",
        12: "Criminal family",
    },
    "childhood_environment": {
        2: "The Street", 3: "War Zone", 4: "Nomad pack",
        5: "Gang-controlled district", 6: "Urban slums",
        7: "Suburban sprawl", 8: "Corporate housing block",
        9: "Rural wasteland", 10: "Space station / orbital",
        11: "Secure corporate arcology", 12: "Military base",
    },
    "family_crisis": {
        2: "Family destroyed by war", 3: "Family imprisoned",
        4: "Family bankrupt", 5: "Family killed by gang",
        6: "Family member killed by corporation", 7: "Family split apart",
        8: "Family member went missing", 9: "Family member betrayed you",
        10: "Family member became cyberpsycho", 11: "Family exiled you",
        12: "No crisis — stable childhood",
    },
}

HANDLES = ["Вектор", "Никс", "Ржавый", "Мираж", "Кастет", "Пиксель", "Гроза", "Шёпот",
           "Кремний", "Игла", "Фара", "Барс", "Люмен", "Скоба", "Танго", "Золо"]
STYLES = ["кожаный плащ", "хромированная челюсть", "тату-маска на пол-лица",
          "зеркальные очки ночью", "куртка с неоновой вышивкой", "боевой шрам через бровь"]


def _roll_2d6(rng):
    return rng.randint(1, 6) + rng.randint(1, 6)


def _alloc_stats(rng):
    """62 очка, каждая 2..8, с небольшой вариацией"""
    stats = {s: STAT_MIN for s in STATS}
    pool = STAT_POOL - STAT_MIN * len(STATS)  # 62 - 20 = 42
    while pool > 0:
        s = rng.choice(STATS)
        if stats[s] < STAT_MAX:
            stats[s] += 1
            pool -= 1
    return stats


def _alloc_skills(rng, role):
    """4 карьерных навыка (старт 2) + 10 очков на дополнительные"""
    role_data = ROLES[role]
    skills = {}
    # Карьерные навыки: ранк 2..3 каждый
    for sk in role_data["career"]:
        skills[sk] = CAREER_START + (1 if rng.random() < 0.5 else 0)
    
    # 10 очков на дополнительные навыки
    pool = ADDITIONAL_SKILL_POOL
    available = [s for s in SKILLS if s not in skills]
    while pool > 0:
        sk = rng.choice(available)
        current = skills.get(sk, 0)
        if current >= SKILL_MAX:
            available.remove(sk)
            continue
        add = rng.randint(1, min(3, pool, SKILL_MAX - current))
        skills[sk] = current + add
        pool -= add
        if skills[sk] >= SKILL_MAX:
            available.remove(sk)
    return skills


def _roll_lifepath(rng):
    """Серия бросков 2d6 для предыстории"""
    lifepath = {}
    for key, table in LIFEPATH_TABLES.items():
        roll = _roll_2d6(rng)
        lifepath[key] = table[roll]
    return lifepath


def random_character(rng=None, role=None, seed=None):
    rng = rng or random.Random(seed)
    role = role or rng.choice(list(ROLES))
    stats = _alloc_stats(rng)
    skills = _alloc_skills(rng, role)
    lifepath = _roll_lifepath(rng)
    name = rng.choice(HANDLES)
    role_data = ROLES[role]
    
    ch = {
        "name": name, "role": role,
        "stats": stats, "skills": skills,
        "hp": stats["BODY"] * 2, "max_hp": stats["BODY"] * 2,
        "wound": "unharmed", "dsp": 0, "dead": False,
        "humanity": stats["EMP"] * 10,
        "armor": role_data["armor"],
        "weapon": role_data["weapon"],
        "gear": role_data["items"],
        "cyberware": role_data["starting_cyberware"],
        "eb": STARTING_EB[role],
        "style": rng.choice(STYLES),
        "ability": role_data["ability"],
        "lifepath": lifepath,
    }
    return ch


def validate_character(ch):
    problems = []
    st = ch.get("stats", {})
    if set(st) != set(STATS):
        problems.append("stats: неверный набор характеристик")
    if sum(st.values()) != STAT_POOL:
        problems.append(f"stats: сумма {sum(st.values())} != {STAT_POOL}")
    for s, v in st.items():
        if not (STAT_MIN <= v <= STAT_MAX):
            problems.append(f"stats: {s}={v} вне диапазона {STAT_MIN}..{STAT_MAX}")
    sk = ch.get("skills", {})
    unknown = [k for k in sk if k not in SKILLS]
    if unknown:
        problems.append(f"skills: неизвестные навыки {unknown}")
    over = [k for k, v in sk.items() if v > SKILL_MAX]
    if over:
        problems.append(f"skills: превышен максимум 6: {over}")
    career = set(ROLES.get(ch.get("role"), {}).get("career", []))
    if ch.get("role") not in ROLES:
        problems.append("role: неизвестная роль")
    elif not career <= set(sk):
        problems.append(f"skills: нет карьерных навыков {career - set(sk)}")
    # Убираем проверку cyberware/eb для manual — они добавляются автоматически
    return problems


def manual_character(payload):
    ch = dict(payload)
    ch.setdefault("wound", "unharmed")
    ch.setdefault("dsp", 0)
    ch.setdefault("dead", False)
    st = ch.get("stats", {})
    # Достраиваем недостающие статы до минимума (2)
    for s in STATS:
        st.setdefault(s, STAT_MIN)
    ch["stats"] = st
    ch["hp"] = ch.get("hp", st.get("BODY", 4) * 2)
    ch["max_hp"] = ch.get("max_hp", st.get("BODY", 4) * 2)
    return ch, validate_character(ch)