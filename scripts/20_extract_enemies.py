# scripts/20_extract_enemies.py
"""Извлечение классов врагов для Cyberpunk RED."""
import json
from pathlib import Path

script_dir = Path(__file__).parent
project_root = script_dir.parent
DATA_DIR = project_root / "data" / "normalized"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# === КЛАССЫ ВРАГОВ ===
# Каждый класс — готовый шаблон для нарратора

ENEMIES = {
    # === УЛИЧНЫЕ БАНДЫ ===
    "bozo_ganger": {
        "name": "Бозо-бандит",
        "faction": "Bozos",
        "tier": "street",
        "stats": {"REF": 6, "BODY": 6, "DEX": 6, "INT": 4, "COOL": 5},
        "skills": {"melee_weapon": 3, "evasion": 2, "perception": 2, "athletics": 2},
        "weapon": "bat",
        "armor": "leathers",
        "hp": 12,
        "special": "Психованные клоуны, атакуют хаотично",
        "behavior": "Агрессивные, непредсказуемые, любят хаос"
    },
    
    "tyger_claw": {
        "name": "Коготь Тигра",
        "faction": "Tyger Claws",
        "tier": "street",
        "stats": {"REF": 7, "BODY": 7, "DEX": 8, "INT": 5, "COOL": 6},
        "skills": {"melee_weapon": 4, "martial_arts": 4, "evasion": 3, "perception": 2},
        "weapon": "machete",
        "armor": "leathers",
        "hp": 14,
        "special": "Японская банда, мастера рукопашного боя",
        "behavior": "Дисциплинированные, атакуют скоординированно"
    },
    
    "animal_ganger": {
        "name": "Член банды Animals",
        "faction": "Animals",
        "tier": "street",
        "stats": {"REF": 6, "BODY": 9, "DEX": 6, "INT": 4, "COOL": 5},
        "skills": {"brawling": 4, "melee_weapon": 3, "athletics": 3, "evasion": 2},
        "weapon": "axe",
        "armor": "kevlar",
        "hp": 18,
        "special": "Тяжёлые, много имплантов для силы",
        "behavior": "Грубая сила, атакуют в лоб"
    },
    
    "maelstromer": {
        "name": "Мальстрёмовец",
        "faction": "Maelstrom",
        "tier": "street",
        "stats": {"REF": 6, "BODY": 7, "DEX": 6, "INT": 7, "COOL": 4},
        "skills": {"interface": 3, "handgun": 3, "evasion": 2, "perception": 3},
        "weapon": "heavy_pistol",
        "armor": "light_armorjack",
        "hp": 14,
        "special": "Киберпсихи с множеством имплантов",
        "behavior": "Параноидальные, агрессивные, используют технику"
    },
    
    "sixth_street": {
        "name": "Член 6th Street",
        "faction": "6th Street",
        "tier": "street",
        "stats": {"REF": 7, "BODY": 7, "DEX": 7, "INT": 5, "COOL": 6},
        "skills": {"handgun": 4, "shoulder_arms": 3, "evasion": 2, "athletics": 3},
        "weapon": "assault_rifle",
        "armor": "kevlar",
        "hp": 14,
        "special": "Милитари-банда, хорошее оружие",
        "behavior": "Тактические, стреляют очередями, используют укрытия"
    },
    
    # === КОРПОРАТИВНЫЕ ===
    "corpo_security": {
        "name": "Корпоративный охранник",
        "faction": "Corpo",
        "tier": "corpo",
        "stats": {"REF": 6, "BODY": 7, "DEX": 6, "INT": 5, "COOL": 6},
        "skills": {"handgun": 3, "perception": 4, "evasion": 2, "deduction": 3},
        "weapon": "heavy_pistol",
        "armor": "light_armorjack",
        "hp": 14,
        "special": "Стандартная охрана корпораций",
        "behavior": "Профессиональные, действуют по протоколу"
    },
    
    "corpo_solo": {
        "name": "Корпоративный боевик",
        "faction": "Corpo",
        "tier": "elite",
        "stats": {"REF": 8, "BODY": 8, "DEX": 8, "INT": 6, "COOL": 7},
        "skills": {"handgun": 5, "melee_weapon": 4, "evasion": 4, "athletics": 4},
        "weapon": "heavy_pistol",
        "armor": "heavy_armorjack",
        "hp": 16,
        "special": "Элитный оперативник, много имплантов",
        "behavior": "Очень опасны, тактичные, используют все ресурсы"
    },
    
    "arasaka_ninja": {
        "name": "Арасака-ниндзя",
        "faction": "Arasaka",
        "tier": "elite",
        "stats": {"REF": 9, "BODY": 8, "DEX": 9, "INT": 7, "COOL": 7},
        "skills": {"melee_weapon": 5, "stealth": 5, "martial_arts": 4, "evasion": 5},
        "weapon": "katana",
        "armor": "metalgear",
        "hp": 16,
        "special": "Элитный ассасин Арасаки",
        "behavior": "Скрытные, атакуют внезапно, смертоносны в ближнем бою"
    },
    
    # === НАЁМНИКИ ===
    "merc_solo": {
        "name": "Наёмник-одиночка",
        "faction": "Freelancer",
        "tier": "elite",
        "stats": {"REF": 8, "BODY": 8, "DEX": 7, "INT": 6, "COOL": 7},
        "skills": {"handgun": 5, "evasion": 4, "athletics": 3, "perception": 4},
        "weapon": "heavy_pistol",
        "armor": "light_armorjack",
        "hp": 16,
        "special": "Опытный наёмник, работает один",
        "behavior": "Осторожные, выбирают выгодные позиции"
    },
    
    "edgerunner": {
        "name": "Эджраннер",
        "faction": "Edgerunner",
        "tier": "elite",
        "stats": {"REF": 7, "BODY": 7, "DEX": 7, "INT": 7, "COOL": 6},
        "skills": {"handgun": 4, "stealth": 4, "interface": 3, "evasion": 3},
        "weapon": "medium_pistol",
        "armor": "light_armorjack",
        "hp": 14,
        "special": "Наёмник с разнообразными навыками",
        "behavior": "Адаптивные, используют все доступные средства"
    },
    
    # === БОССЫ ===
    "gang_leader": {
        "name": "Главарь банды",
        "faction": "Gang",
        "tier": "boss",
        "stats": {"REF": 8, "BODY": 9, "DEX": 8, "INT": 7, "COOL": 8},
        "skills": {"handgun": 5, "melee_weapon": 4, "persuasion": 5, "leadership": 5},
        "weapon": "heavy_pistol",
        "armor": "medium_armorjack",
        "hp": 18,
        "special": "Лидер банды, сильные социальные навыки",
        "behavior": "Командует подчинёнными, не боится прямого боя"
    },
    
    "corpo_exec": {
        "name": "Корпоративный директор",
        "faction": "Corpo",
        "tier": "boss",
        "stats": {"REF": 6, "BODY": 6, "DEX": 6, "INT": 9, "COOL": 9},
        "skills": {"persuasion": 6, "deduction": 6, "trading": 6, "bribery": 5},
        "weapon": "heavy_pistol",
        "armor": "light_armorjack",
        "hp": 12,
        "special": "Топ-менеджер корпорации",
        "behavior": "Использует влияние и ресурсы, редко дерётся сам"
    },
}

# === УРОВНИ СЛОЖНОСТИ (для нарратора) ===
ENEMY_TIERS = {
    "street": {"difficulty": 1, "threat": "Низкая угроза", "count": "2-4"},
    "corpo": {"difficulty": 2, "threat": "Средняя угроза", "count": "2-3"},
    "elite": {"difficulty": 3, "threat": "Высокая угроза", "count": "1-2"},
    "boss": {"difficulty": 4, "threat": "Экстремальная угроза", "count": "1"},
}

# === СООТВЕТСТВИЕ ФРАКЦИЯМ (для контекста) ===
FACTION_ENEMIES = {
    "Bozos": ["bozo_ganger"],
    "Tyger Claws": ["tyger_claw"],
    "Animals": ["animal_ganger"],
    "Maelstrom": ["maelstromer"],
    "6th Street": ["sixth_street"],
    "Corpo": ["corpo_security", "corpo_solo", "corpo_exec"],
    "Arasaka": ["arasaka_ninja", "corpo_solo", "corpo_exec"],
    "Militech": ["corpo_security", "corpo_solo"],
    "Freelancer": ["merc_solo", "edgerunner"],
}


def main():
    data = {
        "enemies": ENEMIES,
        "tiers": ENEMY_TIERS,
        "faction_enemies": FACTION_ENEMIES,
    }
    
    path = DATA_DIR / "enemies.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Создано: {path}")
    print(f"  - {len(ENEMIES)} классов врагов")
    print(f"  - {len(ENEMY_TIERS)} уровней сложности")
    print(f"  - {len(FACTION_ENEMIES)} фракций с привязкой врагов")


if __name__ == "__main__":
    main()