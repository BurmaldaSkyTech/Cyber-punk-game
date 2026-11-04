# backend/inventory.py
"""Инвентарь персонажа, переносимый вес/слоты и покупки."""
import json
from pathlib import Path

_data_dir = Path(__file__).parent.parent / "data" / "normalized"


def _load_json(filename, default=None):
    path = _data_dir / filename
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


WEAPONS = _load_json("weapons_full.json", {})
ARMOR = _load_json("armor_full.json", {})
CYBERWARE = _load_json("cyberware_full.json", {})
GEAR = {
    "medkit": {"name": "Мед-аптечка", "category": "gear", "price": 100},
    "toolkit": {"name": "Набор инструментов", "category": "gear", "price": 200},
    "cam_jammer": {"name": "Глушилка камер", "category": "gear", "price": 500},
    "fake_pass": {"name": "Фальшивый пропуск", "category": "gear", "price": 300},
    "grapnel": {"name": "Крюк-кошка", "category": "gear", "price": 100},
    "agent": {"name": "Агент", "category": "gear", "price": 500},
    "radio": {"name": "Рация", "category": "gear", "price": 100},
}

# Сколько слотов занимает предмет по категории
ITEM_SLOTS = {
    "pistol": 1,
    "rifle": 2,
    "melee": 1,
    "explosive": 1,
    "heavy": 3,
    "energy": 1,
    "armor": 0,
    "cyberware": 0,
    "gear": 1,
    "misc": 1,
}


def item_info(key):
    """Ищет предмет во всех таблицах данных."""
    if key in WEAPONS:
        data = dict(WEAPONS[key])
        data.setdefault("category", "misc")
        return data

    if key in ARMOR:
        data = dict(ARMOR[key])
        data["category"] = "armor"
        return data

    if key in CYBERWARE:
        data = dict(CYBERWARE[key])
        data["category"] = "cyberware"
        return data

    if key in GEAR:
        return dict(GEAR[key])

    return {
        "name": key,
        "category": "misc",
        "price": 0,
    }


def capacity(character):
    """Количество слотов инвентаря: 5 + BODY."""
    body = character.get("stats", {}).get("BODY", 5)
    return 5 + body


def used_slots(character):
    """Сколько слотов занято предметами в инвентаре."""
    total = 0
    for key in character.get("inventory", []):
        info = item_info(key)
        category = info.get("category", "misc")
        total += ITEM_SLOTS.get(category, 1)
    return total


def add_item(character, key, qty=1):
    """Добавляет предмет в инвентарь, если хватает слотов."""
    if qty <= 0:
        return {"success": False, "reason": "Неверное количество"}

    info = item_info(key)
    category = info.get("category", "misc")
    slots_needed = ITEM_SLOTS.get(category, 1) * qty

    if used_slots(character) + slots_needed > capacity(character):
        return {"success": False, "reason": "Инвентарь переполнен"}

    character.setdefault("inventory", []).extend([key] * qty)
    return {"success": True, "item": key, "qty": qty}


def remove_item(character, key, qty=1):
    """Убирает предмет из инвентаря."""
    inventory = character.get("inventory", [])
    removed = 0

    for _ in range(qty):
        if key in inventory:
            inventory.remove(key)
            removed += 1
        else:
            break

    if removed == 0:
        return {"success": False, "reason": "Предмета нет в инвентаре"}

    return {"success": True, "item": key, "removed": removed}


def has_item(character, key, qty=1):
    """Проверяет, есть ли предмет в нужном количестве."""
    return character.get("inventory", []).count(key) >= qty


def buy_item(character, key, qty=1):
    """Покупает предмет, если хватает эдди и слотов."""
    info = item_info(key)
    price = info.get("price", 0) * qty

    eb = character.get("eb", 0)
    if eb < price:
        return {"success": False, "reason": "Недостаточно эдди"}

    result = add_item(character, key, qty=qty)
    if not result["success"]:
        return result

    character["eb"] = eb - price
    result["price"] = price
    result["eb_left"] = character["eb"]
    return result