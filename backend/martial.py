# backend/martial.py
"""Система боевых искусств для Cyberpunk RED.

Стили и приёмы:
- Каждый стиль даёт доступ к набору приёмов
- Приёмы дают бонусы к урону, специальные эффекты (block, disarm, throw)
- Применение приёма требует броска martial_arts навыка
"""
import json
from pathlib import Path

_data_dir = Path(__file__).parent.parent / "data" / "normalized"


def _load_json(filename, default=None):
    path = _data_dir / filename
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


MA_DATA = _load_json("martial_arts.json", {})
STYLES = MA_DATA.get("styles", {})
MOVES = MA_DATA.get("moves", {})


def get_style(style_key):
    """Возвращает данные стиля."""
    return STYLES.get(style_key)


def get_move(move_key):
    """Возвращает данные приёма."""
    return MOVES.get(move_key)


def list_styles():
    """Список всех доступных стилей."""
    return list(STYLES.keys())


def get_style_moves(style_key):
    """Приёмы стиля."""
    style = get_style(style_key)
    if not style:
        return []
    return style.get("moves", [])


def can_use_style(character, style_key):
    """Проверяет, может ли персонаж использовать стиль."""
    if style_key not in STYLES:
        return False, "Неизвестный стиль"
    # Нужен навык martial_arts >= 2
    ma_skill = character.get("skills", {}).get("martial_arts", 0)
    if ma_skill < 2:
        return False, "Нужен навык martial_arts 2+ для боевых искусств"
    return True, ""


def apply_move_bonus(move_key, base_damage):
    """Применяет бонус от стиля к базовому урону."""
    # Ищем стиль, которому принадлежит приём
    for style_key, style in STYLES.items():
        if move_key in style.get("moves", []):
            bonus = style.get("damage_bonus", 0)
            return base_damage + bonus
    return base_damage


def get_move_effect(move_key):
    """Возвращает специальный эффект приёма.
    
    Эффекты:
    - block: уменьшает урон от атаки противника
    - sweep: сбивает с ног (цель теряет ход)
    - disarm: выбивает оружие
    - throw: бросок (урон + падение)
    - choke: удушение (доп. урон каждый ход)
    """
    move = get_move(move_key)
    if not move:
        return None, ""
    
    desc = move.get("desc", "")
    
    # Определяем эффект по описанию
    if "блок" in desc.lower() or "block" in move_key:
        return "block", "уменьшает входящий урон"
    if "подсечк" in desc.lower() or "sweep" in move_key:
        return "sweep", "цель сбита с ног"
    if "разоруж" in desc.lower() or "disarm" in move_key:
        return "disarm", "выбивает оружие"
    if "бросок" in desc.lower() or "throw" in move_key:
        return "throw", "бросает цель на землю"
    if "удуш" in desc.lower() or "choke" in move_key:
        return "choke", "удушение, доп. урон"
    if "рычаг" in desc.lower() or "armbar" in move_key:
        return "armbar", "болевой приём, цель не может действовать"
    
    return None, desc