# backend/body.py
"""Модульность тела персонажа и установка киберимплантов.

Правила:
- У каждого импланта есть слот: brain, eye, ear, arm, leg, body, none.
- Количество слотов ограничено.
- При установке импланта персонаж теряет человечность.
- Если человечность падает до 0, персонаж получает риск киберпсихоза.
"""
import json
import random
from pathlib import Path

_data_dir = Path(__file__).parent.parent / "data" / "normalized"


def _load_json(filename, default=None):
    path = _data_dir / filename
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


CYBERWARE = _load_json("cyberware_full.json", {})

# Допустимое количество слотов по зонам тела
BODY_SLOTS = {
    "brain": 1,
    "eye": 2,
    "ear": 2,
    "arm": 2,
    "leg": 2,
    "body": 3,
    "none": 99,
}


def roll_dice_notation(notation, rng=None):
    """Бросает кубики по нотации вида 1d6, 2d6, 0. Возвращает сумму."""
    rng = rng or random
    if notation in (None, "", "0", 0):
        return 0

    if isinstance(notation, int):
        return notation

    notation = str(notation).lower()
    if "d" not in notation:
        try:
            return int(notation)
        except ValueError:
            return 0

    left, right = notation.split("d", 1)
    count = int(left) if left.strip() else 1
    sides = int(right) if right.strip() else 6

    if count <= 0 or sides <= 0:
        return 0

    return sum(rng.randint(1, sides) for _ in range(count))


def get_cyberware(ware_key):
    """Возвращает данные импланта по ключу."""
    return CYBERWARE.get(ware_key)


def installed_by_slot(character):
    """Считает, сколько имплантов стоит в каждом слоте."""
    counts = {}
    for ware_key in character.get("cyberware", []):
        ware = CYBERWARE.get(ware_key)
        if not ware:
            continue
        slot = ware.get("slot", "none")
        counts[slot] = counts.get(slot, 0) + 1
    return counts


def can_install(character, ware_key):
    """Проверяет, можно ли установить имплант."""
    ware = CYBERWARE.get(ware_key)
    if not ware:
        return False, "Неизвестный имплант"

    if ware_key in character.get("cyberware", []):
        return False, "Имплант уже установлен"

    slot = ware.get("slot", "none")
    max_slots = BODY_SLOTS.get(slot, 1)
    current_slots = installed_by_slot(character).get(slot, 0)

    if current_slots >= max_slots:
        return False, f"Нет свободного слота: {slot}"

    return True, ""


def install_cyberware(character, ware_key, pay_eb=False, rng=None):
    """Устанавливает имплант персонажу.

    Если pay_eb=True, списывает цену из character["eb"].
    """
    ok, reason = can_install(character, ware_key)
    if not ok:
        return {"success": False, "reason": reason}

    ware = CYBERWARE[ware_key]
    price = ware.get("price", 0)

    if pay_eb:
        eb = character.get("eb", 0)
        if eb < price:
            return {"success": False, "reason": "Недостаточно эдди"}
        character["eb"] = eb - price

    character.setdefault("cyberware", []).append(ware_key)

    humanity_loss = roll_dice_notation(ware.get("humanity_loss", "0"), rng=rng)
    old_humanity = character.get("humanity", 0)
    new_humanity = max(0, old_humanity - humanity_loss)

    character["humanity"] = new_humanity
    if new_humanity <= 0:
        character["cyberpsycho_risk"] = True

    return {
        "success": True,
        "ware": ware_key,
        "slot": ware.get("slot", "none"),
        "price": price,
        "humanity_loss": humanity_loss,
        "humanity": new_humanity,
        "cyberpsycho_risk": character.get("cyberpsycho_risk", False),
    }


def remove_cyberware(character, ware_key):
    """Удаляет имплант без восстановления человечности."""
    cyberware = character.get("cyberware", [])
    if ware_key not in cyberware:
        return {"success": False, "reason": "Имплант не установлен"}

    cyberware.remove(ware_key)
    return {"success": True, "ware": ware_key}