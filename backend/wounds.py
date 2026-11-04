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