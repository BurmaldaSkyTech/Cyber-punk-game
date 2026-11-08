# backend/crafting.py
"""Система крафта для роли Tech в Cyberpunk RED.

Механики:
- Рецепты: компоненты + проверка TECH+навык против DV
- Провал тратит компоненты без результата
- Ремонт сломанных предметов
"""

RECIPES = {
    "pipe_shotgun": {
        "name": "Самодельный дробовик",
        "components": {"scrap_metal": 2, "springs": 1, "weapon_parts": 1},
        "skill": "weaponstech",
        "dv": 13,
        "result": "shotgun",
        "desc": "Грубый, но надёжный",
    },
    "makeshift_armor": {
        "name": "Самодельный кевларовый жилет",
        "components": {"armor_plates": 2, "plastics": 1},
        "skill": "basic_tech",
        "dv": 15,
        "result": "kevlar",
        "desc": "Кустарная броня",
    },
    "emp_grenade": {
        "name": "ЭМИ-граната",
        "components": {"electronics": 1, "chemicals": 1},
        "skill": "electronics_security_tech",
        "dv": 17,
        "result": "emp_grenade",
        "desc": "Выжигает электронику и киберимпланты",
    },
    "cam_jammer_craft": {
        "name": "Глушилка камер",
        "components": {"electronics": 2, "optics": 1},
        "skill": "electronics_security_tech",
        "dv": 17,
        "result": "cam_jammer",
        "desc": "Отключает камеры в радиусе действия",
    },
    "medkit_craft": {
        "name": "Полевая аптечка",
        "components": {"chemicals": 2, "plastics": 1},
        "skill": "pharmaceuticals",
        "dv": 15,
        "result": "medkit",
        "desc": "Стимуляторы и бинты",
    },
    "cyber_repair_kit": {
        "name": "Ремкомплект киберимплантов",
        "components": {"electronics": 1, "weapon_parts": 1},
        "skill": "cybertech",
        "dv": 17,
        "result": "cyber_repair_kit",
        "desc": "Для полевого ремонта имплантов",
    },
}


def get_recipe(key):
    """Возвращает рецепт по ключу."""
    return RECIPES.get(key)


def list_recipes():
    """Список всех рецептов."""
    return list(RECIPES.keys())


def missing_components(character, recipe):
    """Возвращает словарь недостающих компонентов."""
    inv = character.get("inventory", [])
    missing = {}
    for comp, qty in recipe.get("components", {}).items():
        have = inv.count(comp)
        if have < qty:
            missing[comp] = qty - have
    return missing


def consume_components(character, recipe):
    """Тратит компоненты рецепта."""
    inv = character.get("inventory", [])
    for comp, qty in recipe.get("components", {}).items():
        for _ in range(qty):
            if comp in inv:
                inv.remove(comp)


def attempt_craft(character, recipe_key, roll_total):
    """Пытается создать предмет.
    
    Компоненты тратятся в любом случае.
    Успех определяется roll_total против DV рецепта.
    """
    recipe = get_recipe(recipe_key)
    if not recipe:
        return {"success": False, "reason": "Неизвестный рецепт"}

    missing = missing_components(character, recipe)
    if missing:
        return {"success": False, "reason": f"Не хватает компонентов: {missing}"}

    consume_components(character, recipe)

    if roll_total >= recipe["dv"]:
        character.setdefault("inventory", []).append(recipe["result"])
        return {
            "success": True,
            "item": recipe["result"],
            "name": recipe["name"],
            "components_spent": recipe["components"],
        }

    return {
        "success": False,
        "reason": "Провал проверки: компоненты испорчены",
        "components_spent": recipe["components"],
    }


def mark_broken(character, item_key):
    """Помечает предмет сломанным."""
    character.setdefault("broken_items", [])
    if item_key not in character["broken_items"]:
        character["broken_items"].append(item_key)
    return {"success": True, "item": item_key}


def repair_item(character, item_key, roll_total, dv=13):
    """Ремонтирует сломанный предмет."""
    broken = character.get("broken_items", [])
    if item_key not in broken:
        return {"success": False, "reason": "Предмет не сломан"}

    if roll_total >= dv:
        broken.remove(item_key)
        return {"success": True, "item": item_key}

    return {"success": False, "reason": "Провал ремонта"}