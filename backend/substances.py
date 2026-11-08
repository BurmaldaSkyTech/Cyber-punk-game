# backend/substances.py
"""Система наркотиков и ядов для Cyberpunk RED.

Механики:
- Наркотики дают временные бонусы/штрафы к статам
- Яды наносят урон или штрафы
- Эффекты имеют длительность (в ходах)
- После окончания действия — синдром отмены
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


SUB_DATA = _load_json("drugs_poisons.json", {})
DRUGS = SUB_DATA.get("drugs", {})
POISONS = SUB_DATA.get("poisons", {})

# Длительность эффектов в ходах (упрощение: 1 час = 6 ходов)
DURATION_TURNS = {
    "stimulant": 6,
    "depressant": 18,
    "hallucinogen": 24,
    "combat_drug": 1,
    "medical": 0,
    "poison": 0,
}

# Парсинг эффектов вида "+2 REF, +1 COOL, +2 MOVE"
def parse_effects(effect_str):
    """Разбирает строку эффектов в словарь {stat: delta}."""
    effects = {}
    if not effect_str:
        return effects
    
    for part in effect_str.split(","):
        part = part.strip()
        if not part:
            continue
        # Ищем паттерн +N STAT или -N STAT
        tokens = part.split()
        if len(tokens) >= 2:
            try:
                delta = int(tokens[0])
                stat = tokens[1].upper()
                if stat in ["INT", "REF", "DEX", "TECH", "COOL", "WILL",
                            "LUCK", "MOVE", "BODY", "EMP"]:
                    effects[stat] = effects.get(stat, 0) + delta
            except ValueError:
                continue
    return effects


def get_substance(key):
    """Возвращает данные вещества (наркотик или яд)."""
    if key in DRUGS:
        data = dict(DRUGS[key])
        data["kind"] = "drug"
        return data
    if key in POISONS:
        data = dict(POISONS[key])
        data["kind"] = "poison"
        return data
    return None


def apply_substance(character, key):
    """Применяет вещество к персонажу.
    
    Возвращает результат:
    - success: bool
    - effects: словарь изменений статов
    - duration: длительность в ходах
    - damage: урон (для ядов и медицинских)
    """
    sub = get_substance(key)
    if not sub:
        return {"success": False, "reason": "Неизвестное вещество"}
    
    kind = sub["kind"]
    result = {"success": True, "substance": key, "kind": kind}
    
    if kind == "drug":
        # Наркотик: временные бонусы/штрафы
        effects = parse_effects(sub.get("effect", ""))
        duration = DURATION_TURNS.get(sub.get("type", "stimulant"), 6)
        
        # Применяем эффекты к статам
        for stat, delta in effects.items():
            if stat in character.get("stats", {}):
                character["stats"][stat] += delta
        
        # Сохраняем активные эффекты для отслеживания
        character.setdefault("active_effects", []).append({
            "key": key,
            "effects": effects,
            "turns_left": duration,
            "withdrawal": sub.get("withdrawal", ""),
        })
        
        result.update({
            "effects": effects,
            "duration": duration,
            "damage": 0,
        })
        
        # Медицинский наркотик лечит
        if sub.get("type") == "medical":
            heal_match = sub.get("effect", "")
            if "HP" in heal_match:
                # Парсим "Восстанавливает 2d6 HP"
                import re
                m = re.search(r"(\d+)d(\d+)", heal_match)
                if m:
                    import random
                    count, sides = int(m.group(1)), int(m.group(2))
                    heal = sum(random.randint(1, sides) for _ in range(count))
                    character["hp"] = min(character["max_hp"], character["hp"] + heal)
                    result["heal"] = heal
    
    elif kind == "poison":
        # Яд: урон и штрафы
        effects = parse_effects(sub.get("effect", ""))
        damage_str = sub.get("damage", "0")
        
        # Парсим урон вида "2d6 (после 10 минут)"
        import re
        m = re.search(r"(\d+)d(\d+)", damage_str)
        damage = 0
        if m:
            import random
            count, sides = int(m.group(1)), int(m.group(2))
            damage = sum(random.randint(1, sides) for _ in range(count))
        
        # Применяем штрафы
        for stat, delta in effects.items():
            if stat in character.get("stats", {}):
                character["stats"][stat] += delta
        
        # Наносим урон
        if damage > 0:
            from .wounds import apply_damage
            damage_result = apply_damage(character, damage)
            character["hp"] = damage_result["hp"]
            character["wound"] = damage_result["wound_state"]
        
        result.update({
            "effects": effects,
            "duration": 0,
            "damage": damage,
        })
    
    return result


def tick_effects(character):
    """Уменьшает длительность активных эффектов и снимает их по истечении.
    
    Вызывается в конце каждого хода.
    """
    expired = []
    for effect in character.get("active_effects", []):
        effect["turns_left"] -= 1
        if effect["turns_left"] <= 0:
            expired.append(effect)
    
    # Снимаем эффекты и применяем синдром отмены
    for effect in expired:
        character["active_effects"].remove(effect)
        # Откатываем бонусы
        for stat, delta in effect["effects"].items():
            if stat in character.get("stats", {}):
                character["stats"][stat] -= delta
    
    return [e["key"] for e in expired]