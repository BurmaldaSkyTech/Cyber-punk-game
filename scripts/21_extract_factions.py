# scripts/21_extract_factions.py
"""Извлечение фракций Night City для Cyberpunk RED."""
import json
from pathlib import Path

script_dir = Path(__file__).parent
project_root = script_dir.parent
DATA_DIR = project_root / "data" / "normalized"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# === ФРАКЦИИ NIGHT CITY ===
FACTIONS = {
    # === КОРПОРАЦИИ ===
    "Arasaka": {
        "type": "corporation",
        "origin": "Япония",
        "specialty": "Безопасность, охрана, оружие",
        "reputation": "Негативная (после 4-й Корп-войны)",
        "territory": "Ограничено в США",
        "allies": ["Militech (иногда)"],
        "enemies": ["Militech (исторически)"],
        "style": "Дисциплина, традиции, эффективность",
        "resources": "Элитные агенты, передовые технологии",
    },
    
    "Militech": {
        "type": "corporation",
        "origin": "США",
        "specialty": "Военные технологии, оружие, бронетехника",
        "reputation": "Нейтральная (после национализации)",
        "territory": "США, союзники",
        "allies": ["Правительство США", "NUSA"],
        "enemies": ["Arasaka (исторически)"],
        "style": "Военная дисциплина, мощь",
        "resources": "Армия, тяжёлое вооружение, авиация",
    },
    
    "Biotechnica": {
        "type": "corporation",
        "origin": "Италия",
        "specialty": "Биотехнологии, ГМО, продовольствие",
        "reputation": "Нейтральная",
        "territory": "Глобально",
        "allies": [],
        "enemies": [],
        "style": "Научный подход, инновации",
        "resources": "Лаборатории, биоинженеры",
    },
    
    "Continental Brands": {
        "type": "corporation",
        "origin": "США",
        "specialty": "Производство кофе и напитков",
        "reputation": "Нейтральная",
        "territory": "Северная Америка",
        "allies": [],
        "enemies": [],
        "style": "Массовое производство",
        "resources": "Кофейные плантации, заводы",
    },
    
    # === БАНДЫ ===
    "Bozos": {
        "type": "gang",
        "origin": "Night City",
        "specialty": "Хаос, разрушение, психотерапия",
        "reputation": "Негативная",
        "territory": "Разбросаны по городу",
        "allies": [],
        "enemies": ["Все"],
        "style": "Психованные клоуны, хаос",
        "resources": "Мало, но непредсказуемы",
        "members": ["bozo_ganger"],
    },
    
    "Tyger Claws": {
        "type": "gang",
        "origin": "Япония (переехали в Night City)",
        "specialty": "Организованная преступность, казино",
        "reputation": "Нейтральная",
        "territory": "Японтаун",
        "allies": [],
        "enemies": ["6th Street"],
        "style": "Японские традиции, дисциплина",
        "resources": "Средние, хорошие бойцы",
        "members": ["tyger_claw"],
    },
    
    "Animals": {
        "type": "gang",
        "origin": "Night City",
        "specialty": "Силовые операции, охрана",
        "reputation": "Нейтральная",
        "territory": "Pacifica, Heywood",
        "allies": [],
        "enemies": [],
        "style": "Грубая сила, тяжёлые импланты",
        "resources": "Средние, физически сильны",
        "members": ["animal_ganger"],
    },
    
    "Maelstrom": {
        "type": "gang",
        "origin": "Night City",
        "specialty": "Киберпанк-культ, технологии",
        "reputation": "Негативная",
        "territory": "Промышленные районы",
        "allies": [],
        "enemies": ["Все"],
        "style": "Киберпсихи, параноидальные",
        "resources": "Средние, много имплантов",
        "members": ["maelstromer"],
    },
    
    "6th Street": {
        "type": "gang",
        "origin": "Night City",
        "specialty": "Милиция, патриотизм",
        "reputation": "Нейтральная",
        "territory": "Santo Domingo",
        "allies": [],
        "enemies": ["Tyger Claws"],
        "style": "Военная дисциплина, американский патриотизм",
        "resources": "Хорошие, много оружия",
        "members": ["sixth_street"],
    },
    
    "Moxes": {
        "type": "gang",
        "origin": "Night City",
        "specialty": "Защита работников секс-индустрии",
        "reputation": "Позитивная",
        "territory": "Downtown",
        "allies": [],
        "enemies": ["Tyger Claws (конфликт интересов)"],
        "style": "Защита слабых, солидарность",
        "resources": "Средние, хорошо организованы",
    },
    
    # === ФРАКЦИИ НАЁМНИКОВ ===
    "Edgerunners": {
        "type": "freelancer",
        "origin": "Night City",
        "specialty": "Наёмная работа",
        "reputation": "Нейтральная",
        "territory": "Везде",
        "allies": ["Фиксеры"],
        "enemies": [],
        "style": "Профессионалы, адаптивность",
        "resources": "Зависит от команды",
        "members": ["edgerunner"],
    },
    
    # === ВЛАСТЬ ===
    "NCPD": {
        "type": "government",
        "origin": "Night City",
        "specialty": "Полиция, закон",
        "reputation": "Нейтральная (коррумпирована)",
        "territory": "Весь город",
        "allies": ["Militech"],
        "enemies": ["Преступники"],
        "style": "Закон и порядок (но с коррупцией)",
        "resources": "Средние, но официальная власть",
    },
    
    "NUSA": {
        "type": "government",
        "origin": "США",
        "specialty": "Федеральное правительство",
        "reputation": "Нейтральная",
        "territory": "США (частично)",
        "allies": ["Militech"],
        "enemies": ["Корпорации (конфликт интересов)"],
        "style": "Бюрократия, федеральная власть",
        "resources": "Ограничены в Night City",
    },
}

# === УРОВНИ ВЛИЯНИЯ ===
FACTION_TIERS = {
    "megacorp": ["Arasaka", "Militech"],
    "major_corp": ["Biotechnica", "Continental Brands"],
    "major_gang": ["Tyger Claws", "6th Street", "Maelstrom"],
    "minor_gang": ["Bozos", "Animals", "Moxes"],
    "freelancer": ["Edgerunners"],
    "government": ["NCPD", "NUSA"],
}


def main():
    data = {
        "factions": FACTIONS,
        "tiers": FACTION_TIERS,
    }
    
    path = DATA_DIR / "factions.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Создано: {path}")
    print(f"  - {len(FACTIONS)} фракций")
    print(f"  - {len(FACTION_TIERS)} категорий влияния")


if __name__ == "__main__":
    main()