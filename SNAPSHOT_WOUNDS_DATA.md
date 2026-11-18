

===== backend/wounds.py (212 строк) =====
# backend/wounds.py
"""Модульная система ранений для Cyberpunk RED.

Пороги ранений:
- HP > max/2: unharmed (здоров)
- HP <= max/2 и > 0: lightly (легко ранен)
- HP <= 0: seriously (серьёзно ранен)
- HP <= -1*max: mortally (смертельно ранен)

Механики:
- Штрафы к действиям при ранах
- Критические травмы по типу урона
- Броски смерти при смертельных ранах
- Стабилизация
"""
import random

# Пороги ранений
WOUND_THRESHOLDS = {
    "unharmed": 1.0,      # HP > max * 1.0
    "lightly": 0.5,       # HP <= max * 0.5
    "seriously": 0.0,     # HP <= 0
    "mortally": -1.0,     # HP <= -max
}

# Штрафы к действиям в зависимости от состояния
WOUND_PENALTIES = {
    "unharmed": 0,
    "lightly": 0,
    "seriously": -2,
    "mortally": -4,
}

# Таблицы критических травм по типу урона
CRITICAL_INJURIES = {
    "melee": {
        1: "Порез: -1 REF на 1 час",
        2: "Ушиб: -1 MOVE на 1 час",
        3: "Растяжение: -2 MOVE на 1 час",
        4: "Перелом пальца: -2 DEX на 2 часа",
        5: "Перелом руки: -4 DEX, оружие выпадает",
        6: "Перелом ноги: -4 MOVE, падение",
        7: "Травма головы: оглушение на 1 ход",
        8: "Пробитие лёгкого: -2 BODY, кашель кровью",
        9: "Повреждение глаза: -2 INT, слепота на 1 глаз",
        10: "Критическое ранение: смертельный бросок",
    },
    "bullet": {
        1: "Царапина: -1 REF на 1 час",
        2: "Ушиб от пули: -1 DEX на 1 час",
        3: "Осколок: -1 BODY, кровотечение",
        4: "Пуля в плечо: -3 DEX, оружие выпадает",
        5: "Пуля в ногу: -3 MOVE, падение",
        6: "Пуля в живот: кровотечение, -2 BODY каждый ход",
        7: "Пуля в голову: оглушение на 2 хода",
        8: "Пуля в лёгкое: -2 BODY, нельзя говорить",
        9: "Разрыв артерии: сильное кровотечение, -3 BODY каждый ход",
        10: "Критическое ранение: смертельный бросок",
    },
    "explosive": {
        1: "Контузия: -1 INT на 1 час",
        2: "Ожоги 1 степени: -1 BODY",
        3: "Осколки: -2 BODY, кровотечение",
        4: "Контузия: оглушение на 1 ход",
        5: "Ожоги 2 степени: -2 BODY на 1 час",
        6: "Потеря пальца: -2 DEX навсегда",
        7: "Ожог глаз: слепота на 1 час",
        8: "Ожоги 3 степени: -4 BODY на 2 часа",
        9: "Отрыв конечности: -6 к соответствующему стату навсегда",
        10: "Критическое ранение: смертельный бросок",
    },
    "energy": {
        1: "Ожог: -1 BODY на 1 час",
        2: "Паралич мышц: -1 MOVE на 1 ход",
        3: "Ожог 2 степени: -2 BODY",
        4: "Поражение нервной системы: -2 REF на 2 хода",
        5: "Ожог 3 степени: -3 BODY на 2 часа",
        6: "Потеря сознания: 1 ход без сознания",
        7: "Ожог глаз: слепота на 1 час",
        8: "Кипение крови: -4 BODY на 1 час",
        9: "Обугливание: -6 BODY, риск смерти",
        10: "Критическое ранение: смертельный бросок",
    },
}

# Соответствие типа оружия типу урона
WEAPON_DAMAGE_TYPE = {
    # Пистолеты и винтовки
    "medium_pistol": "bullet",
    "heavy_pistol": "bullet",
    "very_heavy_pistol": "bullet",
    "assault_rifle": "bullet",
    "sniper_rifle": "bullet",
    "smg": "bullet",
    "shotgun": "bullet",
    
    # Холодное оружие
    "knife": "melee",
    "machete": "melee",
    "axe": "melee",
    "chainsaw": "melee",
    "bat": "melee",
    
    # Взрывчатка
    "grenade": "explosive",
    "rocket_launcher": "explosive",
    
    # Энергетическое
    "microwave_gun": "energy",
    "laser_pistol": "energy",
    "flamethrower": "energy",
}


def get_wound_state(hp, max_hp):
    """Определяет состояние ранения по текущим и максимальным HP."""
    if max_hp <= 0:
        return "mortally"

    if hp >= max_hp:
        return "unharmed"

    if hp > max_hp / 2:
        return "lightly"

    if hp > 0:
        return "seriously"

    return "mortally"


def get_wound_penalty(wound_state):
    """Возвращает штраф к действиям в зависимости от состояния."""
    return WOUND_PENALTIES.get(wound_state, 0)


def roll_critical_injury(damage_type="bullet", rng=None):
    """Бросает 1d10 и возвращает критическую травму по типу урона."""
    rng = rng or random.Random()
    roll = rng.randint(1, 10)
    table = CRITICAL_INJURIES.get(damage_type, CRITICAL_INJURIES["bullet"])
    return table[roll]


def determine_damage_type(weapon_key):
    """Определяет тип урона по ключу оружия."""
    return WEAPON_DAMAGE_TYPE.get(weapon_key, "bullet")


def apply_damage(target, damage, weapon_key=None):
    """Применяет урон к цели и возвращает результат.
    
    Возвращает словарь:
    - hp: новые HP
    - wound_state: новое состояние ранения
    - penalty: штраф к действиям
    - critical_injury: текст критической травмы (если была)
    - death_save: нужен ли бросок смерти
    - dead: умерла ли цель
    """
    max_hp = target.get("max_hp", 10)
    new_hp = target.get("hp", 10) - damage
    
    wound_state = get_wound_state(new_hp, max_hp)
    penalty = get_wound_penalty(wound_state)
    
    # Критическая травма при серьёзном ранении
    critical_injury = None
    if wound_state in ("seriously", "mortally"):
        damage_type = determine_damage_type(weapon_key) if weapon_key else "bullet"
        critical_injury = roll_critical_injury(damage_type)
    
    # Бросок смерти при смертельном ранении
    death_save = wound_state == "mortally"
    
    return {
        "hp": new_hp,
        "wound_state": wound_state,
        "penalty": penalty,
        "critical_injury": critical_injury,
        "death_save": death_save,
        "dead": False,  # Устанавливается отдельно после броска смерти
    }


def death_save(target, rng=None):
    """Бросок смерти: 1d10, нужно меньше BODY, иначе смерть."""
    rng = rng or random.Random()
    body = target.get("stats", {}).get("BODY", 5)
    roll = rng.randint(1, 10)
    
    if roll > body:
        return {"dead": True, "roll": roll, "body": body,
                "result": f"Бросок {roll} > BODY {body}: смерть"}
    return {"dead": False, "roll": roll, "body": body,
            "result": f"Бросок {roll} <= BODY {body}: стабилизация"}


def stabilize(target, medic_skill, rng=None):
    """Стабилизация цели с критической травмой.
    
    Проверка: 1d10 + medic_skill против DV 13.
    """
    rng = rng or random.Random()
    roll = rng.randint(1, 10)
    total = roll + medic_skill
    
    if total >= 13:
        return {"success": True, "total": total,
                "result": "Цель стабилизирована"}
    return {"success": False, "total": total,
            "result": "Стабилизация не удалась"}

===== ИНВЕНТАРЬ data/ (19 json) =====

--- data\extracted\toc.json (44765 байт) — list, 553 записей ---
образец: [{"level": 1, "title": "Front Cover", "page": 1}, {"level": 1, "title": "Title Page", "page": 4}]

--- data\normalized\armor_full.json (1440 байт) — dict, 9 ключей ---
ключи: leathers, kevlar, light_armorjack, bodyweight_suit, medium_armorjack, heavy_armorjack, flak, metalgear, bulletproof_shield
образец: {"leathers": {"name": "Кожаная куртка", "sp": 4, "penalty": "None", "conceal": "excellent", "price": 20}, "kevlar": {"name": "Кевлар", "sp": 7, "penalty": "None", "conceal": "good", "price": 50}}

--- data\normalized\cyberware_full.json (3083 байт) — dict, 14 ключей ---
ключи: Neural Link, Interface Plugs, Basic Cyberoptic, Cyberoptic with options, Basic Cyberaudio, Cyberarm, Cyberleg, Subdermal Armor, Subdermal Pocket, Skinweave, Cyberdeck, Chipware Socket, Sandevistan, Kerenzikov
образец: {"Neural Link": {"name": "Нейролинк", "slot": "brain", "humanity_loss": "1d6", "price": 100, "desc": "Базовый интерфейс для всех имплантов"}, "Interface Plugs": {"name": "Интерфейсные разъёмы", "slot": "brain", "humanity_loss": "1d6", "price": 200, "desc": "Для подключения к Сети (Нетраннер)"}}

--- data\normalized\drugs_poisons.json (3151 байт) — dict, 2 ключей ---
ключи: drugs, poisons
образец: {"drugs": {"smash": {"name": "Smash", "type": "stimulant", "duration": "1 час", "effect": "+2 REF, +1 COOL, +2 MOVE", "withdrawal": "-2 REF, -2 COOL после действия", "addiction": "средняя", "price": 20, "desc": "Популярный стимулятор"}, "boost": {"name": "Boost", "type": "stimulant", "duration": "2 часа", "effect": "+2 INT, +1 WILL", "withdrawal": "-1 INT после действия", "addiction": "низкая", "price": 50, "desc": "Усиливает интеллект"}, "slam": {"name": "Slam", "type": "depressant", "duration": "3 часа", "effect": "+2 BODY, +2 WILL, -2 REF", "withdrawal": "-2 BODY после действия", "addiction": "высокая", "price": 30, "desc": "Усиливает выносливость"}, "acid": {"name": "Acid", "type": "hallucinogen", "duration": "4 часа", "effect": "+2 EMP, -2 INT, галлюцинации", "withdrawal": "депрессия, паранойя", "addiction": "средняя", "price": 15, "desc": "Галлюциноген"}, "berserker": {"name": "Ber

--- data\normalized\enemies.json (8896 байт) — dict, 3 ключей ---
ключи: enemies, tiers, faction_enemies
образец: {"enemies": {"bozo_ganger": {"name": "Бозо-бандит", "faction": "Bozos", "tier": "street", "stats": {"REF": 6, "BODY": 6, "DEX": 6, "INT": 4, "COOL": 5}, "skills": {"melee_weapon": 3, "evasion": 2, "perception": 2, "athletics": 2}, "weapon": "bat", "armor": "leathers", "hp": 12, "special": "Психованные клоуны, атакуют хаотично", "behavior": "Агрессивные, непредсказуемые, любят хаос"}, "tyger_claw": {"name": "Коготь Тигра", "faction": "Tyger Claws", "tier": "street", "stats": {"REF": 7, "BODY": 7, "DEX": 8, "INT": 5, "COOL": 6}, "skills": {"melee_weapon": 4, "martial_arts": 4, "evasion": 3, "perception": 2}, "weapon": "machete", "armor": "leathers", "hp": 14, "special": "Японская банда, мастера рукопашного боя", "behavior": "Дисциплинированные, атакуют скоординированно"}, "animal_ganger": {"name": "Член банды Animals", "faction": "Animals", "tier": "street", "stats": {"REF": 6, "BODY": 9, 

--- data\normalized\factions.json (7252 байт) — dict, 2 ключей ---
ключи: factions, tiers
образец: {"factions": {"Arasaka": {"type": "corporation", "origin": "Япония", "specialty": "Безопасность, охрана, оружие", "reputation": "Негативная (после 4-й Корп-войны)", "territory": "Ограничено в США", "allies": ["Militech (иногда)"], "enemies": ["Militech (исторически)"], "style": "Дисциплина, традиции, эффективность", "resources": "Элитные агенты, передовые технологии"}, "Militech": {"type": "corporation", "origin": "США", "specialty": "Военные технологии, оружие, бронетехника", "reputation": "Нейтральная (после национализации)", "territory": "США, союзники", "allies": ["Правительство США", "NUSA"], "enemies": ["Arasaka (исторически)"], "style": "Военная дисциплина, мощь", "resources": "Армия, тяжёлое вооружение, авиация"}, "Biotechnica": {"type": "corporation", "origin": "Италия", "specialty": "Биотехнологии, ГМО, продовольствие", "reputation": "Нейтральная", "territory": "Глобально", "al

--- data\normalized\lifepath_tables.json (5847 байт) — dict, 2 ключей ---
ключи: general, role_specific
образец: {"general": {"personality_traits": ["Shy and secretive", "Rebellious, antisocial and violent", "Arrogant, proud and aloof", "Moody, rash and headstrong", "Picky, fussy and nervous", "Stable and serious", "Goofy and lighthearted", "Sneaky and deceptive", "Intellectual and detached", "Friendly and outgoing", "Protective and nurturing", "Driven and passionate"], "clothing_style": ["Generic Chic (standard, colorful)", "Leisurewear (comfort, flexibility)", "Urban Flash (flashy, streetwear)", "Businesswear (formal, professional)", "High Fashion (exclusive designer)", "Bohemian (vintage, hippie)", "Bag Lady Chic (homeless, mismatched)", "Gang Colors (gang-affiliated)", "Nomad Leathers (tribal, practical)", "Asia Pop (anime, bright)", "Military (camouflage, tactical)", "Rocker Style (leather, studs)"], "hairstyle": ["Mohawk", "Long and ratty", "Short and spiked", "Wild and unkempt", "Braided or 

--- data\normalized\martial_arts.json (2798 байт) — dict, 2 ключей ---
ключи: styles, moves
образец: {"styles": {"Karate": {"name": "Каратэ", "damage_bonus": 0, "special": "block", "moves": ["block", "strike", "kick", "sweep"]}, "Taekwondo": {"name": "Тхэквондо", "damage_bonus": 1, "special": "kick", "moves": ["high_kick", "spin_kick", "axe_kick", "jump_kick"]}, "Boxing": {"name": "Бокс", "damage_bonus": 1, "special": "punch", "moves": ["jab", "hook", "uppercut", "block"]}, "Muay Thai": {"name": "Муай-тай", "damage_bonus": 1, "special": "clinch", "moves": ["elbow", "knee", "clinch", "low_kick"]}, "Capoeira": {"name": "Капоэйра", "damage_bonus": 0, "special": "dodge", "moves": ["spin_kick", "sweep", "cartwheel", "takedown"]}, "Krav Maga": {"name": "Крав-мага", "damage_bonus": 1, "special": "disarm", "moves": ["disarm", "strike", "throw", "choke"]}, "Judo": {"name": "Дзюдо", "damage_bonus": 0, "special": "throw", "moves": ["throw", "hold", "armbar", "choke"]}}, "moves": {"block": {"name":

--- data\normalized\netrunning.json (5107 байт) — dict, 3 ключей ---
ключи: cyberdecks, programs, architectures
образец: {"cyberdecks": {"basic_deck": {"name": "Базовая дека", "speed": 1, "slots": 4, "price": 1000, "desc": "Стартовая дека для новичков"}, "standard_deck": {"name": "Стандартная дека", "speed": 2, "slots": 6, "price": 2000, "desc": "Рабочая лошадка нетраннера"}, "advanced_deck": {"name": "Продвинутая дека", "speed": 3, "slots": 8, "price": 5000, "desc": "Хорошая дека для серьёзных операций"}, "elite_deck": {"name": "Элитная дека", "speed": 4, "slots": 10, "price": 10000, "desc": "Лучшая дека на чёрном рынке"}}, "programs": {"see_ya": {"name": "See Ya", "type": "attack", "class": "demon", "cost": "MU 1", "effect": "Атакует программу противника", "damage": "2d6", "price": 500}, "hellbolt": {"name": "Hellbolt", "type": "attack", "class": "demon", "cost": "MU 2", "effect": "Мощная атака на программу", "damage": "3d6", "price": 800}, "poison_flatline": {"name": "Poison Flatline", "type": "attack",

--- data\normalized\skills_full.json (8591 байт) — dict, 63 ключей ---
ключи: athletics, brawling, concentration, contortionist, dance, drive_land_vehicle, evasion, handgun, heavy_weapons, martial_arts, melee_weapon, pilot_air_vehicle, pilot_sea_vehicle, riding, shoulder_arms, autofire, stealth, accounting, conceal_reveal_object, criminology, cryptography, deduction, education, gamble, language, library_search, lip_reading, local_expert, perception, science, tactics, tracking, wilderness_survival, air_vehicle_tech, basic_tech, cybertech, demolitions, electronics_security_tech, first_aid, forgery
образец: {"athletics": {"stat": "BODY", "category": "physical", "desc": "Акробатика, лазание, бег, прыжки"}, "brawling": {"stat": "REF", "category": "combat", "desc": "Рукопашный бой без оружия"}}

--- data\normalized\vehicles.json (4085 байт) — dict, 2 ключей ---
ключи: vehicles, categories
образец: {"vehicles": {"bike_city": {"name": "Городской мотоцикл", "category": "bike", "speed": 80, "armor": "SP 4", "seats": 1, "weapons": [], "price": 2000, "skill": "drive_land_vehicle", "notes": "Быстрый, манёвренный, мало брони"}, "bike_road": {"name": "Дорожный мотоцикл", "category": "bike", "speed": 120, "armor": "SP 6", "seats": 2, "weapons": [], "price": 4000, "skill": "drive_land_vehicle", "notes": "Для дальних поездок"}, "bike_offroad": {"name": "Внедорожный мотоцикл", "category": "bike", "speed": 100, "armor": "SP 8", "seats": 1, "weapons": [], "price": 5000, "skill": "drive_land_vehicle", "notes": "Для плохих дорог"}, "car_compact": {"name": "Компактный автомобиль", "category": "car", "speed": 100, "armor": "SP 6", "seats": 4, "weapons": [], "price": 10000, "skill": "drive_land_vehicle", "notes": "Экономичный городской"}, "car_sedan": {"name": "Седан", "category": "car", "speed": 120

--- data\normalized\weapons_full.json (3743 байт) — dict, 16 ключей ---
ключи: medium_pistol, heavy_pistol, very_heavy_pistol, smg, heavy_smg, shotgun, assault_rifle, sniper_rifle, rocket_launcher, knife, machete, bat, axe, chainsaw, grenade, flamethrower
образец: {"medium_pistol": {"name": "Средний пистолет", "category": "pistol", "skill": "handgun", "damage": "2d6", "rof": 2, "mag": 12, "conceal": "yes", "range": 50, "price": 50, "notes": "Стандартный пистолет"}, "heavy_pistol": {"name": "Тяжёлый пистолет", "category": "pistol", "skill": "handgun", "damage": "3d6", "rof": 2, "mag": 8, "conceal": "yes", "range": 50, "price": 100, "notes": "Мощный пистолет"}}

--- data\rules\armor.json (2496 байт) — dict, 3 ключей ---
ключи: pack, book, entries
образец: {"pack": "armor", "book": "Cyberpunk RED Core Rulebook"}

--- data\rules\combat.json (7384 байт) — dict, 3 ключей ---
ключи: pack, book, entries
образец: {"pack": "combat", "book": "Cyberpunk RED Core Rulebook"}

--- data\rules\creation.json (4364 байт) — dict, 3 ключей ---
ключи: pack, book, entries
образец: {"pack": "creation", "book": "Cyberpunk RED Core Rulebook"}

--- data\rules\cyberware.json (580 байт) — dict, 3 ключей ---
ключи: pack, book, entries
образец: {"pack": "cyberware", "book": "Cyberpunk RED Core Rulebook"}

--- data\rules\gear.json (564 байт) — dict, 3 ключей ---
ключи: pack, book, entries
образец: {"pack": "gear", "book": "Cyberpunk RED Core Rulebook"}

--- data\rules\netrunning.json (1069 байт) — dict, 3 ключей ---
ключи: pack, book, entries
образец: {"pack": "netrunning", "book": "Cyberpunk RED Core Rulebook"}

--- data\rules\weapons.json (4173 байт) — dict, 3 ключей ---
ключи: pack, book, entries
образец: {"pack": "weapons", "book": "Cyberpunk RED Core Rulebook"}


===== ПОКРЫТИЕ КАТАЛОГА =====
skills_full: data\normalized\skills_full.json
cyberware_full: data\normalized\cyberware_full.json
martial_arts: data\normalized\martial_arts.json
martial_moves: НЕ НАЙДЕН
weapons_full: data\normalized\weapons_full.json
armor_full: data\normalized\armor_full.json
drugs: data\normalized\drugs_poisons.json
poisons: data\normalized\drugs_poisons.json
programs: НЕ НАЙДЕН
cyberdecks: НЕ НАЙДЕН
architectures: НЕ НАЙДЕН
vehicles: data\normalized\vehicles.json
enemies: data\normalized\enemies.json
factions: data\normalized\factions.json
