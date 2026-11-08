# backend/vehicles.py
"""Система транспорта и погонь для Cyberpunk RED.

Механики:
- Владение и посадка в транспорт
- Погони: дистанция 0..4 (вплотную .. отрыв), contested-броски REF + навык вождения
- Таран: урон от разницы скоростей и брони
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


VEHICLES_DATA = _load_json("vehicles.json", {})
VEHICLES = VEHICLES_DATA.get("vehicles", {})
CATEGORIES = VEHICLES_DATA.get("categories", {})

# Дистанции погони
RANGE_NAMES = {
    0: "вплотную (можно таранить и брать на абордаж)",
    1: "близко (огонь из оружия без штрафов)",
    2: "средне (огонь со штрафом -2)",
    3: "далеко (огонь со штрафом -4)",
    4: "отрыв (цель уходит)",
}


def get_vehicle(key):
    """Возвращает данные транспорта."""
    return VEHICLES.get(key)


def parse_sp(armor_str):
    """Разбирает строку брони 'SP 12' в число."""
    if not armor_str:
        return 0
    try:
        return int(str(armor_str).replace("SP", "").strip())
    except ValueError:
        return 0


def driving_skill(vehicle_key):
    """Навык, необходимый для управления транспортом."""
    v = get_vehicle(vehicle_key)
    return (v or {}).get("skill", "drive_land_vehicle")


def can_board(character, vehicle_key):
    """Проверяет, может ли персонаж сесть в транспорт."""
    v = get_vehicle(vehicle_key)
    if not v:
        return False, "Неизвестный транспорт"
    owned = character.get("vehicles", [])
    if owned and vehicle_key not in owned:
        return False, "Транспорт не принадлежит персонажу"
    if character.get("vehicle"):
        return False, "Персонаж уже в транспорте"
    return True, ""


def board_vehicle(character, vehicle_key):
    """Сажает персонажа в транспорт."""
    ok, reason = can_board(character, vehicle_key)
    if not ok:
        return {"success": False, "reason": reason}
    character["vehicle"] = vehicle_key
    return {"success": True, "vehicle": vehicle_key}


def exit_vehicle(character):
    """Персонаж покидает транспорт."""
    v = character.get("vehicle")
    if not v:
        return {"success": False, "reason": "Персонаж не в транспорте"}
    character["vehicle"] = None
    return {"success": True, "vehicle": v}


def buy_vehicle(character, vehicle_key):
    """Покупка транспорта за эдди."""
    v = get_vehicle(vehicle_key)
    if not v:
        return {"success": False, "reason": "Неизвестный транспорт"}
    price = v.get("price", 0)
    if character.get("eb", 0) < price:
        return {"success": False, "reason": "Недостаточно эдди"}
    character["eb"] -= price
    character.setdefault("vehicles", []).append(vehicle_key)
    return {"success": True, "vehicle": vehicle_key, "price": price}


def start_chase(pursuer_key, target_key):
    """Начинает погоню. Дистанция стартует со средней (2)."""
    return {
        "pursuer": pursuer_key,
        "target": target_key,
        "pursuer_vehicle": pursuer_key,
        "target_vehicle": target_key,
        "range": 2,
        "rounds": 0,
        "status": "active",
    }


def chase_step(chase, pursuer_total, target_total):
    """Один раунд погони: contested-броски вождения.
    
    Победитель сдвигает дистанцию: преследователь уменьшает, цель увеличивает.
    """
    if chase.get("status") != "active":
        return chase

    diff = pursuer_total - target_total
    if diff > 0:
        chase["range"] = max(0, chase["range"] - 1)
    elif diff < 0:
        chase["range"] = min(4, chase["range"] + 1)

    chase["rounds"] += 1

    if chase["range"] == 0:
        chase["status"] = "caught"
    elif chase["range"] >= 4:
        chase["status"] = "escaped"

    chase["range_name"] = RANGE_NAMES[chase["range"]]
    return chase


def ram_damage(attacker_vehicle_key, target_vehicle_key, rng=None):
    """Урон от тарана: 3d6 + разница скоростей / 20, минус броня цели."""
    rng = rng or random
    a = get_vehicle(attacker_vehicle_key) or {}
    t = get_vehicle(target_vehicle_key) or {}

    base = sum(rng.randint(1, 6) for _ in range(3))
    speed_diff = (a.get("speed", 0) - t.get("speed", 0)) // 20
    raw = max(1, base + speed_diff)

    sp = parse_sp(t.get("armor"))
    net = max(0, raw - sp)
    return {"raw": raw, "sp": sp, "net": net}