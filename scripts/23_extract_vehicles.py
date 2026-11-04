# scripts/23_extract_vehicles.py
"""Извлечение данных транспорта для Cyberpunk RED."""
import json
from pathlib import Path

script_dir = Path(__file__).parent
project_root = script_dir.parent
DATA_DIR = project_root / "data" / "normalized"
DATA_DIR.mkdir(parents=True, exist_ok=True)


VEHICLES = {
    # Мотоциклы
    "bike_city": {
        "name": "Городской мотоцикл",
        "category": "bike",
        "speed": 80,
        "armor": "SP 4",
        "seats": 1,
        "weapons": [],
        "price": 2000,
        "skill": "drive_land_vehicle",
        "notes": "Быстрый, манёвренный, мало брони"
    },
    "bike_road": {
        "name": "Дорожный мотоцикл",
        "category": "bike",
        "speed": 120,
        "armor": "SP 6",
        "seats": 2,
        "weapons": [],
        "price": 4000,
        "skill": "drive_land_vehicle",
        "notes": "Для дальних поездок"
    },
    "bike_offroad": {
        "name": "Внедорожный мотоцикл",
        "category": "bike",
        "speed": 100,
        "armor": "SP 8",
        "seats": 1,
        "weapons": [],
        "price": 5000,
        "skill": "drive_land_vehicle",
        "notes": "Для плохих дорог"
    },
    
    # Автомобили
    "car_compact": {
        "name": "Компактный автомобиль",
        "category": "car",
        "speed": 100,
        "armor": "SP 6",
        "seats": 4,
        "weapons": [],
        "price": 10000,
        "skill": "drive_land_vehicle",
        "notes": "Экономичный городской"
    },
    "car_sedan": {
        "name": "Седан",
        "category": "car",
        "speed": 120,
        "armor": "SP 8",
        "seats": 5,
        "weapons": [],
        "price": 20000,
        "skill": "drive_land_vehicle",
        "notes": "Стандартный корпоративный"
    },
    "car_sport": {
        "name": "Спортивный автомобиль",
        "category": "car",
        "speed": 180,
        "armor": "SP 6",
        "seats": 2,
        "weapons": [],
        "price": 50000,
        "skill": "drive_land_vehicle",
        "notes": "Быстрый, дорогой, заметный"
    },
    "car_armor": {
        "name": "Бронированный автомобиль",
        "category": "car",
        "speed": 100,
        "armor": "SP 20",
        "seats": 4,
        "weapons": ["smg_turret"],
        "price": 80000,
        "skill": "drive_land_vehicle",
        "notes": "Тяжёлая защита, оружие"
    },
    
    # Грузовики и фургоны
    "van": {
        "name": "Фургон",
        "category": "truck",
        "speed": 80,
        "armor": "SP 10",
        "seats": 6,
        "weapons": [],
        "price": 30000,
        "skill": "drive_land_vehicle",
        "notes": "Для перевозки грузов и людей"
    },
    "truck_heavy": {
        "name": "Тяжёлый грузовик",
        "category": "truck",
        "speed": 60,
        "armor": "SP 15",
        "seats": 3,
        "weapons": [],
        "price": 60000,
        "skill": "drive_land_vehicle",
        "notes": "Для больших грузов"
    },
    
    # Воздушный транспорт
    "av_4": {
        "name": "AV-4",
        "category": "air",
        "speed": 300,
        "armor": "SP 12",
        "seats": 6,
        "weapons": [],
        "price": 200000,
        "skill": "pilot_air_vehicle",
        "notes": "Воздушный транспорт, вертикальный взлёт"
    },
    "av_9": {
        "name": "AV-9",
        "category": "air",
        "speed": 500,
        "armor": "SP 20",
        "seats": 8,
        "weapons": ["missile_pod"],
        "price": 1000000,
        "skill": "pilot_air_vehicle",
        "notes": "Элитный воздушный транспорт, оружие"
    },
    
    # Морской транспорт
    "boat_small": {
        "name": "Малая лодка",
        "category": "sea",
        "speed": 40,
        "armor": "SP 6",
        "seats": 4,
        "weapons": [],
        "price": 15000,
        "skill": "pilot_sea_vehicle",
        "notes": "Для рек и побережья"
    },
}

# Категории транспорта
VEHICLE_CATEGORIES = {
    "bike": "Мотоциклы",
    "car": "Автомобили",
    "truck": "Грузовики и фургоны",
    "air": "Воздушный транспорт",
    "sea": "Морской транспорт",
}


def main():
    data = {
        "vehicles": VEHICLES,
        "categories": VEHICLE_CATEGORIES,
    }
    
    path = DATA_DIR / "vehicles.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Создано: {path}")
    print(f"  - {len(VEHICLES)} видов транспорта")
    print(f"  - {len(VEHICLE_CATEGORIES)} категорий")


if __name__ == "__main__":
    main()