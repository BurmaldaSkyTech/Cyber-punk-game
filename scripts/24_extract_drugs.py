# scripts/24_extract_drugs.py
"""Извлечение данных наркотиков и ядов для Cyberpunk RED."""
import json
from pathlib import Path

script_dir = Path(__file__).parent
project_root = script_dir.parent
DATA_DIR = project_root / "data" / "normalized"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# === НАРКОТИКИ ===
DRUGS = {
    # Стимуляторы
    "smash": {
        "name": "Smash",
        "type": "stimulant",
        "duration": "1 час",
        "effect": "+2 REF, +1 COOL, +2 MOVE",
        "withdrawal": "-2 REF, -2 COOL после действия",
        "addiction": "средняя",
        "price": 20,
        "desc": "Популярный стимулятор"
    },
    "boost": {
        "name": "Boost",
        "type": "stimulant",
        "duration": "2 часа",
        "effect": "+2 INT, +1 WILL",
        "withdrawal": "-1 INT после действия",
        "addiction": "низкая",
        "price": 50,
        "desc": "Усиливает интеллект"
    },
    
    # Депрессанты
    "slam": {
        "name": "Slam",
        "type": "depressant",
        "duration": "3 часа",
        "effect": "+2 BODY, +2 WILL, -2 REF",
        "withdrawal": "-2 BODY после действия",
        "addiction": "высокая",
        "price": 30,
        "desc": "Усиливает выносливость"
    },
    
    # Галлюциногены
    "acid": {
        "name": "Acid",
        "type": "hallucinogen",
        "duration": "4 часа",
        "effect": "+2 EMP, -2 INT, галлюцинации",
        "withdrawal": "депрессия, паранойя",
        "addiction": "средняя",
        "price": 15,
        "desc": "Галлюциноген"
    },
    
    # Боевые наркотики
    "berserker": {
        "name": "Berserker",
        "type": "combat_drug",
        "duration": "10 минут",
        "effect": "+2 BODY, +2 WILL, игнорировать боль",
        "withdrawal": "агрессия, -2 COOL",
        "addiction": "высокая",
        "price": 100,
        "desc": "Боевой наркотик"
    },
    
    # Лечебные
    "speedheal": {
        "name": "Speedheal",
        "type": "medical",
        "duration": "мгновенно",
        "effect": "Восстанавливает 2d6 HP",
        "withdrawal": "нет",
        "addiction": "нет",
        "price": 200,
        "desc": "Быстрое исцеление"
    },
}


# === ЯДЫ ===
POISONS = {
    "toxin_weak": {
        "name": "Слабый токсин",
        "type": "poison",
        "effect": "-2 к всем статам на 1 час",
        "damage": "1d6 (после 10 минут)",
        "price": 50,
        "desc": "Лёгкое отравление"
    },
    "toxin_medium": {
        "name": "Средний токсин",
        "type": "poison",
        "effect": "-3 к REF и DEX на 2 часа",
        "damage": "2d6 (после 10 минут)",
        "price": 150,
        "desc": "Серьёзное отравление"
    },
    "toxin_strong": {
        "name": "Сильный токсин",
        "type": "poison",
        "effect": "-4 к всем статам, паралич",
        "damage": "4d6 (после 5 минут)",
        "price": 500,
        "desc": "Смертельный яд"
    },
    "neurotoxin": {
        "name": "Нейротоксин",
        "type": "poison",
        "effect": "Паралич, потеря сознания",
        "damage": "3d6 к мозгу",
        "price": 1000,
        "desc": "Нервно-паралитический"
    },
}


def main():
    data = {
        "drugs": DRUGS,
        "poisons": POISONS,
    }
    
    path = DATA_DIR / "drugs_poisons.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Создано: {path}")
    print(f"  - {len(DRUGS)} наркотиков")
    print(f"  - {len(POISONS)} ядов")


if __name__ == "__main__":
    main()