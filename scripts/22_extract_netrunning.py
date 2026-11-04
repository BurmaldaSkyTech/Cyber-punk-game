# scripts/22_extract_netrunning.py
"""Извлечение данных нетраннинга для Cyberpunk RED."""
import json
from pathlib import Path

script_dir = Path(__file__).parent
project_root = script_dir.parent
DATA_DIR = project_root / "data" / "normalized"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# === КИБЕРДЕКИ ===
CYBERDECKS = {
    "basic_deck": {
        "name": "Базовая дека",
        "speed": 1, "slots": 4, "price": 1000,
        "desc": "Стартовая дека для новичков"
    },
    "standard_deck": {
        "name": "Стандартная дека",
        "speed": 2, "slots": 6, "price": 2000,
        "desc": "Рабочая лошадка нетраннера"
    },
    "advanced_deck": {
        "name": "Продвинутая дека",
        "speed": 3, "slots": 8, "price": 5000,
        "desc": "Хорошая дека для серьёзных операций"
    },
    "elite_deck": {
        "name": "Элитная дека",
        "speed": 4, "slots": 10, "price": 10000,
        "desc": "Лучшая дека на чёрном рынке"
    },
}


# === ПРОГРАММЫ (СКРИПТЫ) ===
PROGRAMS = {
    # Атакующие программы (демоны)
    "see_ya": {
        "name": "See Ya",
        "type": "attack",
        "class": "demon",
        "cost": "MU 1",
        "effect": "Атакует программу противника",
        "damage": "2d6",
        "price": 500
    },
    "hellbolt": {
        "name": "Hellbolt",
        "type": "attack",
        "class": "demon",
        "cost": "MU 2",
        "effect": "Мощная атака на программу",
        "damage": "3d6",
        "price": 800
    },
    "poison_flatline": {
        "name": "Poison Flatline",
        "type": "attack",
        "class": "demon",
        "cost": "MU 3",
        "effect": "Уничтожает программу противника",
        "damage": "4d6",
        "price": 1000
    },
    "killer": {
        "name": "Killer",
        "type": "attack",
        "class": "anti-personnel",
        "cost": "MU 2",
        "effect": "Атакует мозг нетраннера через интерфейс",
        "damage": "3d6 (к телу)",
        "price": 1500
    },
    
    # Защитные программы
    "armor": {
        "name": "Armor",
        "type": "defense",
        "class": "shield",
        "cost": "MU 2",
        "effect": "Защищает от атак на программы",
        "protection": "SP 10",
        "price": 500
    },
    "firewall": {
        "name": "Firewall",
        "type": "defense",
        "class": "shield",
        "cost": "MU 3",
        "effect": "Защищает от атак на нетраннера",
        "protection": "SP 15",
        "price": 800
    },
    "flak": {
        "name": "Flak",
        "type": "defense",
        "class": "shield",
        "cost": "MU 4",
        "effect": "Полная защита от всех атак",
        "protection": "SP 20",
        "price": 1200
    },
    
    # Утилиты
    "speedy_gonzales": {
        "name": "Speedy Gonzales",
        "type": "utility",
        "class": "boost",
        "cost": "MU 1",
        "effect": "Увеличивает скорость входа на +2",
        "price": 300
    },
    "worm": {
        "name": "Worm",
        "type": "utility",
        "class": "access",
        "cost": "MU 2",
        "effect": "Обходит простые защитные программы",
        "price": 400
    },
    "deckbreaker": {
        "name": "Deckbreaker",
        "type": "utility",
        "class": "attack",
        "cost": "MU 3",
        "effect": "Ломает деку противника",
        "damage": "2d6 (к деке)",
        "price": 1000
    },
    "datateste": {
        "name": "Datateste",
        "type": "utility",
        "class": "access",
        "cost": "MU 1",
        "effect": "Читает данные без взлома",
        "price": 200
    },
    
    # Специальные
    "aiviewer": {
        "name": "AI Viewer",
        "type": "utility",
        "class": "special",
        "cost": "MU 2",
        "effect": "Обнаруживает ИИ в системе",
        "price": 600
    },
    "genie": {
        "name": "Genie",
        "type": "utility",
        "class": "special",
        "cost": "MU 5",
        "effect": "Создаёт временные программы",
        "price": 2000
    },
}


# === АРХИТЕКТУРЫ (уровни сложности сети) ===
ARCHITECTURES = {
    "simple": {
        "name": "Простая",
        "dv": 13,
        "floors": 2,
        "programs": ["see_ya"],
        "desc": "Домашняя сеть или мелкий бизнес"
    },
    "standard": {
        "name": "Стандартная",
        "dv": 15,
        "floors": 4,
        "programs": ["see_ya", "armor"],
        "desc": "Корпоративная сеть среднего уровня"
    },
    "advanced": {
        "name": "Продвинутая",
        "dv": 17,
        "floors": 6,
        "programs": ["hellbolt", "armor", "worm"],
        "desc": "Защищённая корпоративная сеть"
    },
    "fortress": {
        "name": "Крепость",
        "dv": 19,
        "floors": 8,
        "programs": ["poison_flatline", "killer", "flak"],
        "desc": "Максимально защищённая сеть (Арасака, Милитех)"
    },
}


def main():
    data = {
        "cyberdecks": CYBERDECKS,
        "programs": PROGRAMS,
        "architectures": ARCHITECTURES,
    }
    
    path = DATA_DIR / "netrunning.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Создано: {path}")
    print(f"  - {len(CYBERDECKS)} кибердек")
    print(f"  - {len(PROGRAMS)} программ")
    print(f"  - {len(ARCHITECTURES)} архитектур")


if __name__ == "__main__":
    main()