# backend/netrunning.py
"""Система нетраннинга для Cyberpunk RED.

Механики:
- Вход в сеть (NET Architecture)
- Использование программ (атакующие, защитные, утилиты)
- Сражения с ICE (Intrusion Countermeasure Electronics)
- Взлом систем и получение данных
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


NETRUNNING_DATA = _load_json("netrunning.json", {})
CYBERDECKS = NETRUNNING_DATA.get("cyberdecks", {})
PROGRAMS = NETRUNNING_DATA.get("programs", {})
ARCHITECTURES = NETRUNNING_DATA.get("architectures", {})


def get_cyberdeck(deck_key):
    """Возвращает данные кибердеки."""
    return CYBERDECKS.get(deck_key)


def get_program(program_key):
    """Возвращает данные программы."""
    return PROGRAMS.get(program_key)


def get_architecture(arch_key):
    """Возвращает данные архитектуры сети."""
    return ARCHITECTURES.get(arch_key)


def calculate_net_stats(character):
    """Вычисляет характеристики нетраннера в сети.
    
    SPEED = INT + deck.speed
    MU (Memory Units) = deck.slots
    """
    int_stat = character.get("stats", {}).get("INT", 5)
    deck_key = character.get("cyberdeck", "basic_deck")
    deck = get_cyberdeck(deck_key)
    
    if not deck:
        deck = {"speed": 1, "slots": 4}
    
    return {
        "speed": int_stat + deck.get("speed", 1),
        "mu_total": deck.get("slots", 4),
        "mu_used": sum(
            get_program(p).get("cost", "MU 0").split()[-1]
            for p in character.get("programs", [])
            if get_program(p)
        ) or 0,
    }


def roll_net_attack(program_key, rng=None):
    """Бросает урон от атакующей программы."""
    rng = rng or random
    program = get_program(program_key)
    if not program or program.get("type") != "attack":
        return 0
    
    damage_notation = program.get("damage", "0")
    if "d" not in damage_notation:
        try:
            return int(damage_notation)
        except ValueError:
            return 0
    
    count, sides = damage_notation.split("d")
    count = int(count) if count else 1
    sides = int(sides) if sides else 6
    
    return sum(rng.randint(1, sides) for _ in range(count))


def enter_architecture(character, arch_key):
    """Нетраннер входит в архитектуру сети.
    
    Возвращает состояние входа:
    - floor: текущий этаж (начинаем с 1)
    - max_floors: максимальное количество этажей
    - dv: сложность архитектуры
    - programs: программы защиты на этажах
    """
    arch = get_architecture(arch_key)
    if not arch:
        return {"success": False, "reason": "Неизвестная архитектура"}
    
    # Проверка наличия Interface Plugs или аналога
    cyberware = character.get("cyberware", [])
    has_interface = any("interface" in c.lower() for c in cyberware)
    
    if not has_interface:
        return {"success": False, "reason": "Нет Interface Plugs для входа в сеть"}
    
    return {
        "success": True,
        "architecture": arch_key,
        "floor": 1,
        "max_floors": arch.get("floors", 2),
        "dv": arch.get("dv", 13),
        "programs": arch.get("programs", []),
    }


def scan_floor(character, net_state):
    """Сканирует текущий этаж на предмет ICE и данных.
    
    Проверка: INT + interface против DV архитектуры.
    """
    int_stat = character.get("stats", {}).get("INT", 5)
    interface_skill = character.get("skills", {}).get("interface", 0)
    
    return {
        "action_type": "skill",
        "skill": "interface",
        "stat_key": "INT",
        "stat": int_stat,
        "skill_level": interface_skill,
        "dv": net_state.get("dv", 13),
        "result": "scan",
    }


def use_program(character, program_key, target=None):
    """Использует программу.
    
    Для атакующих: возвращает урон
    Для защитных: возвращает SP защиты
    Для утилит: возвращает эффект
    """
    program = get_program(program_key)
    if not program:
        return {"success": False, "reason": "Неизвестная программа"}
    
    prog_type = program.get("type")
    
    if prog_type == "attack":
        damage = roll_net_attack(program_key)
        return {
            "success": True,
            "type": "attack",
            "program": program_key,
            "damage": damage,
            "target": target,
        }
    
    elif prog_type == "defense":
        sp = program.get("protection", "SP 0")
        sp_value = int(sp.split()[-1]) if sp else 0
        return {
            "success": True,
            "type": "defense",
            "program": program_key,
            "sp": sp_value,
        }
    
    elif prog_type == "utility":
        return {
            "success": True,
            "type": "utility",
            "program": program_key,
            "effect": program.get("effect", ""),
        }
    
    return {"success": False, "reason": "Неизвестный тип программы"}


def ascend_floor(net_state):
    """Поднимается на следующий этаж архитектуры."""
    current = net_state.get("floor", 1)
    max_floors = net_state.get("max_floors", 2)
    
    if current >= max_floors:
        return {"success": False, "reason": "Достигнут последний этаж"}
    
    net_state["floor"] = current + 1
    return {"success": True, "new_floor": current + 1}


def get_net_ice(net_state):
    """Возвращает ICE (защитные программы) на текущем этаже."""
    floor = net_state.get("floor", 1)
    all_programs = net_state.get("programs", [])
    
    # Простая логика: на каждом этаже есть часть программ
    programs_per_floor = max(1, len(all_programs) // net_state.get("max_floors", 1))
    start_idx = (floor - 1) * programs_per_floor
    end_idx = start_idx + programs_per_floor
    
    return all_programs[start_idx:end_idx]


def _mu_cost(prog):
    raw = str((prog or {}).get("cost", "0"))
    digits = "".join(ch for ch in raw if ch.isdigit())
    return int(digits) if digits else 0


def calculate_net_stats(character):
    """Исправлено: MU считаются числами, а не строками."""
    int_stat = (character.get("stats") or {}).get("INT", 5)
    deck = get_cyberdeck(character.get("cyberdeck", "basic_deck")) or {"speed": 1, "slots": 4}
    progs = [get_program(p) for p in character.get("programs", [])]
    return {"speed": int_stat + int(deck.get("speed", 1)),
            "mu_total": int(deck.get("slots", 4)),
            "mu_used": sum(_mu_cost(p) for p in progs if p)}
