# scripts/19_extract_game_data.py
"""Извлечение полных игровых данных для CPR RED.
Создаёт структурированные JSON в data/normalized/.
"""
import json
from pathlib import Path

script_dir = Path(__file__).parent
project_root = script_dir.parent
DATA_DIR = project_root / "data" / "normalized"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# === ПОЛНЫЙ СПИСОК НАВЫКОВ (51 навык + поднавыки) ===
SKILLS_FULL = {
    # REF-based (боевые и физические)
    "athletics": {"stat": "BODY", "category": "physical", "desc": "Акробатика, лазание, бег, прыжки"},
    "brawling": {"stat": "REF", "category": "combat", "desc": "Рукопашный бой без оружия"},
    "concentration": {"stat": "WILL", "category": "mental", "desc": "Концентрация под давлением"},
    "contortionist": {"stat": "REF", "category": "physical", "desc": "Гибкость тела"},
    "dance": {"stat": "REF", "category": "social", "desc": "Танец"},
    "drive_land_vehicle": {"stat": "REF", "category": "vehicle", "desc": "Вождение наземного транспорта"},
    "evasion": {"stat": "REF", "category": "combat", "desc": "Уклонение от атак"},
    "handgun": {"stat": "REF", "category": "combat", "desc": "Пистолеты и револьверы"},
    "heavy_weapons": {"stat": "REF", "category": "combat", "desc": "Тяжёлое оружие: ракетницы, станковые"},
    "martial_arts": {"stat": "REF", "category": "combat", "desc": "Боевые искусства (выбор стиля)"},
    "melee_weapon": {"stat": "REF", "category": "combat", "desc": "Холодное оружие: ножи, топоры, биты"},
    "pilot_air_vehicle": {"stat": "REF", "category": "vehicle", "desc": "Пилотирование воздушного транспорта"},
    "pilot_sea_vehicle": {"stat": "REF", "category": "vehicle", "desc": "Управление морским транспортом"},
    "riding": {"stat": "REF", "category": "vehicle", "desc": "Верховая езда"},
    "shoulder_arms": {"stat": "REF", "category": "combat", "desc": "Винтовки и дробовики"},
    "autofire": {"stat": "REF", "category": "combat", "desc": "Огонь очередями из автоматического оружия"},
    "stealth": {"stat": "REF", "category": "stealth", "desc": "Скрытность и бесшумное передвижение"},
    
    # INT-based (интеллект)
    "accounting": {"stat": "INT", "category": "knowledge", "desc": "Финансы и бухгалтерия"},
    "conceal_reveal_object": {"stat": "INT", "category": "stealth", "desc": "Прятать и находить предметы"},
    "criminology": {"stat": "INT", "category": "knowledge", "desc": "Криминалистика и расследования"},
    "cryptography": {"stat": "INT", "category": "knowledge", "desc": "Шифрование и дешифровка"},
    "deduction": {"stat": "INT", "category": "knowledge", "desc": "Дедукция и анализ"},
    "education": {"stat": "INT", "category": "knowledge", "desc": "Общее образование"},
    "gamble": {"stat": "INT", "category": "knowledge", "desc": "Азартные игры"},
    "language": {"stat": "INT", "category": "knowledge", "desc": "Иностранные языки", "subskills": True},
    "library_search": {"stat": "INT", "category": "knowledge", "desc": "Поиск информации в базах данных"},
    "lip_reading": {"stat": "INT", "category": "knowledge", "desc": "Чтение по губам"},
    "local_expert": {"stat": "INT", "category": "knowledge", "desc": "Знание конкретной локации", "subskills": True},
    "perception": {"stat": "INT", "category": "awareness", "desc": "Внимательность и наблюдение"},
    "science": {"stat": "INT", "category": "knowledge", "desc": "Научные знания", "subskills": True},
    "tactics": {"stat": "INT", "category": "knowledge", "desc": "Тактика и стратегия"},
    "tracking": {"stat": "INT", "category": "awareness", "desc": "Слежка и преследование"},
    "wilderness_survival": {"stat": "INT", "category": "knowledge", "desc": "Выживание в дикой природе"},
    
    # TECH-based (технические)
    "air_vehicle_tech": {"stat": "TECH", "category": "tech", "desc": "Ремонт воздушного транспорта"},
    "basic_tech": {"stat": "TECH", "category": "tech", "desc": "Базовая техника и ремонт"},
    "cybertech": {"stat": "TECH", "category": "tech", "desc": "Установка и ремонт киберимплантов"},
    "demolitions": {"stat": "TECH", "category": "tech", "desc": "Взрывчатка и подрыв"},
    "electronics_security_tech": {"stat": "TECH", "category": "tech", "desc": "Электроника и системы безопасности"},
    "first_aid": {"stat": "TECH", "category": "medical", "desc": "Первая помощь"},
    "forgery": {"stat": "TECH", "category": "tech", "desc": "Подделка документов"},
    "land_vehicle_tech": {"stat": "TECH", "category": "tech", "desc": "Ремонт наземного транспорта"},
    "paint_draw_photography": {"stat": "TECH", "category": "creative", "desc": "Рисование, фотография"},
    "paramedic": {"stat": "TECH", "category": "medical", "desc": "Парамедицинская помощь"},
    "pharmaceuticals": {"stat": "TECH", "category": "medical", "desc": "Фармакология"},
    "pick_lock": {"stat": "TECH", "category": "stealth", "desc": "Взлом замков"},
    "pick_pocket": {"stat": "TECH", "category": "stealth", "desc": "Карманные кражи"},
    "sea_vehicle_tech": {"stat": "TECH", "category": "tech", "desc": "Ремонт морского транспорта"},
    "weaponstech": {"stat": "TECH", "category": "tech", "desc": "Ремонт и модификация оружия"},
    
    # COOL-based (социальные)
    "acting": {"stat": "COOL", "category": "social", "desc": "Актёрское мастерство"},
    "bribery": {"stat": "COOL", "category": "social", "desc": "Подкуп"},
    "conversation": {"stat": "COOL", "category": "social", "desc": "Ведение беседы"},
    "human_perception": {"stat": "COOL", "category": "social", "desc": "Чтение эмоций и намерений"},
    "interrogation": {"stat": "COOL", "category": "social", "desc": "Допрос"},
    "persuasion": {"stat": "COOL", "category": "social", "desc": "Убеждение"},
    "personal_grooming": {"stat": "COOL", "category": "social", "desc": "Уход за собой, внешний вид"},
    "streetwise": {"stat": "COOL", "category": "social", "desc": "Уличная смекалка"},
    "trading": {"stat": "COOL", "category": "social", "desc": "Торговля и бартер"},
    "wardrobe_style": {"stat": "COOL", "category": "social", "desc": "Стиль одежды"},
    
    # EMP-based (эмпатия)
    "performance": {"stat": "EMP", "category": "creative", "desc": "Музыка, выступление"},
    
    # Специальные навыки ролей
    "interface": {"stat": "INT", "category": "netrunner", "desc": "Вход в Сеть (только Нетраннер)", "role_locked": True},
    "programming": {"stat": "INT", "category": "netrunner", "desc": "Программирование (только Нетраннер)", "role_locked": True},
    "tracking_cybernetics": {"stat": "INT", "category": "medtech", "desc": "Медтехника: кибернетика (только Медтех)", "role_locked": True},
    "surgery": {"stat": "TECH", "category": "medtech", "desc": "Хирургия (только Медтех)", "role_locked": True},
    
    # Поднавыки (заполняются по запросу)
    # "language_<name>", "local_expert_<area>", "science_<field>"
}


# === ОРУЖИЕ (полный список по категориям) ===
WEAPONS_FULL = {
    # Пистолеты
    "medium_pistol": {"name": "Средний пистолет", "category": "pistol", "skill": "handgun",
                      "damage": "2d6", "ro": 2, "mag": 12, "conceal": "good",
                      "range": 50, "price": 50, "notes": "Стандартный пистолет"},
    "heavy_pistol": {"name": "Тяжёлый пистолет", "category": "pistol", "skill": "handgun",
                     "damage": "3d6", "ro": 2, "mag": 8, "conceal": "poor",
                     "range": 50, "price": 100, "notes": "Мощный пистолет"},
    "very_heavy_pistol": {"name": "Очень тяжёлый пистолет", "category": "pistol", "skill": "handgun",
                          "damage": "4d6", "ro": 1, "mag": 6, "conceal": "impossible",
                          "range": 50, "price": 150, "notes": "Дезерт Игл и аналоги"},
    
    # Винтовки
    "shotgun": {"name": "Дробовик", "category": "rifle", "skill": "shoulder_arms",
                "damage": "5d6", "ro": 2, "mag": 4, "conceal": "impossible",
                "range": 30, "price": 150, "notes": "Мощный на ближней дистанции"},
    "assault_rifle": {"name": "Штурмовая винтовка", "category": "rifle", "skill": "shoulder_arms",
                      "damage": "5d6", "ro": 3, "mag": 30, "conceal": "impossible",
                      "range": 400, "price": 500, "notes": "Автоматический огонь"},
    "sniper_rifle": {"name": "Снайперская винтовка", "category": "rifle", "skill": "shoulder_arms",
                     "damage": "5d6", "ro": 1, "mag": 5, "conceal": "impossible",
                     "range": 1000, "price": 1000, "notes": "Дальнобойность"},
    "smg": {"name": "Пистолет-пулемёт", "category": "rifle", "skill": "shoulder_arms",
            "damage": "3d6", "ro": 3, "mag": 30, "conceal": "poor",
            "range": 100, "price": 300, "notes": "Автоматический огонь"},
    
    # Холодное оружие
    "knife": {"name": "Нож", "category": "melee", "skill": "melee_weapon",
              "damage": "1d6", "ro": 2, "conceal": "excellent", "price": 10},
    "machete": {"name": "Мачете", "category": "melee", "skill": "melee_weapon",
                "damage": "2d6", "ro": 2, "conceal": "poor", "price": 20},
    "axe": {"name": "Топор", "category": "melee", "skill": "melee_weapon",
            "damage": "3d6", "ro": 2, "conceal": "impossible", "price": 30},
    "chainsaw": {"name": "Бензопила", "category": "melee", "skill": "melee_weapon",
                 "damage": "4d6", "ro": 2, "conceal": "impossible", "price": 100},
    "bat": {"name": "Бита", "category": "melee", "skill": "melee_weapon",
            "damage": "2d6", "ro": 2, "conceal": "poor", "price": 10},
    
    # Тяжёлое оружие
    "grenade": {"name": "Граната", "category": "explosive", "skill": "athletics",
                "damage": "6d6", "ro": 1, "aoe": 5, "conceal": "good", "price": 100},
    "rocket_launcher": {"name": "Ракетница", "category": "heavy", "skill": "heavy_weapons",
                        "damage": "8d6", "ro": 1, "aoe": 10, "conceal": "impossible", "price": 2000},
    "flamethrower": {"name": "Огнемёт", "category": "heavy", "skill": "heavy_weapons",
                     "damage": "4d6", "ro": 2, "aoe": 3, "conceal": "impossible", "price": 1000},
    
    # Экзотика
    "microwave_gun": {"name": "Микроволновка", "category": "energy", "skill": "handgun",
                      "damage": "2d6", "ro": 2, "special": "stun", "price": 500},
    "laser_pistol": {"name": "Лазерный пистолет", "category": "energy", "skill": "handgun",
                     "damage": "3d6", "ro": 2, "price": 800},
}


# === БРОНЯ (все уровни) ===
ARMOR_FULL = {
    "leathers": {"name": "Кожаная куртка", "sp": 4, "conceal": "excellent", "price": 20},
    "kevlar": {"name": "Кевлар", "sp": 7, "conceal": "good", "price": 100},
    "light_armorjack": {"name": "Лёгкая броня", "sp": 11, "conceal": "good", "price": 200},
    "metalgear": {"name": "Металлическая броня", "sp": 12, "conceal": "poor", "price": 300},
    "medium_armorjack": {"name": "Средняя броня", "sp": 12, "conceal": "poor", "price": 300},
    "heavy_armorjack": {"name": "Тяжёлая броня", "sp": 14, "conceal": "impossible", "price": 500},
    "flak": {"name": "Флак-жилет", "sp": 15, "conceal": "impossible", "price": 600},
    "bodyplate": {"name": "Бронекостюм", "sp": 18, "conceal": "impossible", "price": 1000},
}


# === КИБЕРИМПЛАНТЫ (с потерей человечности) ===
CYBERWARE_FULL = {
    "Neural Link": {"name": "Нейролинк", "slot": "brain", "humanity_loss": "1d6",
                    "price": 100, "desc": "Базовый интерфейс для всех имплантов"},
    "Interface Plugs": {"name": "Интерфейсные разъёмы", "slot": "brain", "humanity_loss": "1d6",
                        "price": 200, "desc": "Для подключения к Сети (Нетраннер)"},
    "Basic Cyberoptic": {"name": "Базовый киберглаз", "slot": "eye", "humanity_loss": "1d6",
                         "price": 200, "desc": "Один слот под опцию"},
    "Cyberoptic with options": {"name": "Киберглаз с опциями", "slot": "eye", "humanity_loss": "2d6",
                                "price": 400, "options": ["infrared", "low_light", "targeting", "teleoptic"]},
    "Basic Cyberaudio": {"name": "Базовая киберушная раковина", "slot": "ear", "humanity_loss": "1d6",
                         "price": 150, "options": ["amplified_hearing", "radio_link", "voice_stress"]},
    "Cyberarm": {"name": "Киберрука", "slot": "arm", "humanity_loss": "2d6", "price": 500,
                 "desc": "Заменяет руку, имеет слоты под оружие и инструменты"},
    "Cyberleg": {"name": "Кибернога", "slot": "leg", "humanity_loss": "2d6", "price": 500,
                 "desc": "Заменяет ногу, улучшает скорость и прыжки"},
    "Subdermal Armor": {"name": "Подкожная броня", "slot": "body", "humanity_loss": "2d6",
                        "price": 1000, "sp": 7, "desc": "Броня под кожей"},
    "Subdermal Pocket": {"name": "Подкожный карман", "slot": "body", "humanity_loss": "1d6",
                         "price": 300, "desc": "Скрытое хранилище"},
    "Skinweave": {"name": "Бронированная кожа", "slot": "body", "humanity_loss": "2d6",
                  "price": 800, "sp": 4, "desc": "Усиленная кожа"},
    "Cyberdeck": {"name": "Кибердека", "slot": "none", "humanity_loss": "0",
                  "price": 1000, "desc": "Для входа в Сеть", "netrunner_only": True},
    "Chipware Socket": {"name": "Разъём для чипов", "slot": "brain", "humanity_loss": "1d6",
                        "price": 500, "desc": "Для установки чипов навыков"},
    "Sandevistan": {"name": "Сандевистан", "slot": "brain", "humanity_loss": "2d6",
                    "price": 2000, "desc": "Ускорение рефлексов: +3 к инициативе"},
    "Kerenzikov": {"name": "Керензиков", "slot": "brain", "humanity_loss": "2d6",
                   "price": 1500, "desc": "Замедление восприятия: +2 к уклонению"},
}


# === БОЕВЫЕ ИСКУССТВА (стили и приёмы) ===
MARTIAL_ARTS = {
    "Karate": {"name": "Каратэ", "damage_bonus": 0, "special": "block",
               "moves": ["block", "strike", "kick", "sweep"]},
    "Taekwondo": {"name": "Тхэквондо", "damage_bonus": 1, "special": "kick",
                  "moves": ["high_kick", "spin_kick", "axe_kick", "jump_kick"]},
    "Boxing": {"name": "Бокс", "damage_bonus": 1, "special": "punch",
               "moves": ["jab", "hook", "uppercut", "block"]},
    "Muay Thai": {"name": "Муай-тай", "damage_bonus": 1, "special": "clinch",
                  "moves": ["elbow", "knee", "clinch", "low_kick"]},
    "Capoeira": {"name": "Капоэйра", "damage_bonus": 0, "special": "dodge",
                 "moves": ["spin_kick", "sweep", "cartwheel", "takedown"]},
    "Krav Maga": {"name": "Крав-мага", "damage_bonus": 1, "special": "disarm",
                  "moves": ["disarm", "strike", "throw", "choke"]},
    "Judo": {"name": "Дзюдо", "damage_bonus": 0, "special": "throw",
             "moves": ["throw", "hold", "armbar", "choke"]},
}

# Приёмы боевых искусств
MARTIAL_MOVES = {
    "block": {"name": "Блок", "desc": "Уменьшает урон от атаки"},
    "strike": {"name": "Удар", "desc": "Стандартный удар"},
    "kick": {"name": "Удар ногой", "desc": "Удар ногой"},
    "high_kick": {"name": "Высокий удар ногой", "desc": "Удар ногой в голову"},
    "sweep": {"name": "Подсечка", "desc": "Сбивает противника с ног"},
    "elbow": {"name": "Удар локтем", "desc": "Короткий мощный удар"},
    "knee": {"name": "Удар коленом", "desc": "Ближний удар"},
    "disarm": {"name": "Разоружение", "desc": "Вырывает оружие из рук"},
    "throw": {"name": "Бросок", "desc": "Бросает противника на землю"},
    "choke": {"name": "Удушение", "desc": "Приём удушения"},
    "armbar": {"name": "Рычаг локтя", "desc": "Болевой приём"},
}


# === КИРОВЫЕ ДАННЫЕ ДЛЯ ИЗВЛЕЧЕНИЯ ===

def save_json(filename, data):
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  ✓ {path.name}")


def main():
    print("Извлечение игровых данных...\n")
    
    save_json("skills_full.json", SKILLS_FULL)
    save_json("weapons_full.json", WEAPONS_FULL)
    save_json("armor_full.json", ARMOR_FULL)
    save_json("cyberware_full.json", CYBERWARE_FULL)
    save_json("martial_arts.json", {"styles": MARTIAL_ARTS, "moves": MARTIAL_MOVES})
    
    print(f"\nСоздано 5 файлов данных в {DATA_DIR}")
    print("\nСледующие шаги:")
    print("  - drugs_poisons.json (наркотики и яды)")
    print("  - vehicles.json (транспорт)")
    print("  - netrunning.json (кибердеки и скрипты)")
    print("  - enemies.json (классы врагов)")
    print("  - factions.json (фракции)")


if __name__ == "__main__":
    main()