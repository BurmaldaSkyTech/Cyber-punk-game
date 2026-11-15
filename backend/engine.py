# backend/engine.py
"""Игровая механика для Cyberpunk RED.
Включает броски, проверки навыков, боёвку, помощь, реакции и модульную систему ранений.
"""
import random
import json
from pathlib import Path
from .wounds import (apply_damage, death_save, get_wound_state,
                     get_wound_penalty, roll_critical_injury, determine_damage_type)
from . import martial
from . import netrunning


# ============================================================
# ЗАГРУЗКА ПОЛНЫХ ДАННЫХ ИЗ ФАЙЛОВ
# ============================================================

_data_dir = Path(__file__).parent.parent / "data" / "normalized"


def _load_json(filename, default=None):
    """Загружает JSON-файл из директории данных."""
    path = _data_dir / filename
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


# Загружаем полные данные
SKILLS_FULL = _load_json("skills_full.json", {})
WEAPONS_FULL = _load_json("weapons_full.json", {})
ARMOR_FULL = _load_json("armor_full.json", {})
CYBERWARE_FULL = _load_json("cyberware_full.json", {})
MARTIAL_ARTS_DATA = _load_json("martial_arts.json", {})
ENEMIES_DATA = _load_json("enemies.json", {})
FACTIONS_DATA = _load_json("factions.json", {})


# ============================================================
# СТАТЫ И НАВЫКИ
# ============================================================

STATS = ["INT", "REF", "DEX", "TECH", "COOL", "WILL", "LUCK", "MOVE", "BODY", "EMP"]

# Базовый словарь навыков (будет дополнен из файлов)
SKILL_STAT = {
    # REF-based
    "athletics": "BODY", "brawling": "REF", "concentration": "WILL",
    "contortionist": "REF", "dance": "REF", "drive_land_vehicle": "REF",
    "evasion": "REF", "handgun": "REF", "heavy_weapons": "REF",
    "martial_arts": "REF", "melee_weapon": "REF", "pilot_air_vehicle": "REF",
    "pilot_sea_vehicle": "REF", "riding": "REF", "shoulder_arms": "REF",
    "autofire": "REF", "stealth": "REF",
    
    # INT-based
    "accounting": "INT", "conceal_reveal_object": "INT", "criminology": "INT",
    "cryptography": "INT", "deduction": "INT", "education": "INT",
    "gamble": "INT", "language": "INT", "library_search": "INT",
    "lip_reading": "INT", "local_expert": "INT", "perception": "INT",
    "science": "INT", "tactics": "INT", "tracking": "INT",
    "wilderness_survival": "INT", "interface": "INT", "programming": "INT",
    
    # TECH-based
    "air_vehicle_tech": "TECH", "basic_tech": "TECH", "cybertech": "TECH",
    "demolitions": "TECH", "electronics_security_tech": "TECH",
    "first_aid": "TECH", "forgery": "TECH", "land_vehicle_tech": "TECH",
    "paint_draw_photography": "TECH", "paramedic": "TECH",
    "pharmaceuticals": "TECH", "pick_lock": "TECH", "pick_pocket": "TECH",
    "sea_vehicle_tech": "TECH", "weaponstech": "TECH",
    
    # COOL-based
    "acting": "COOL", "bribery": "COOL", "conversation": "COOL",
    "human_perception": "COOL", "interrogation": "COOL", "persuasion": "COOL",
    "personal_grooming": "COOL", "streetwise": "COOL", "trading": "COOL",
    "wardrobe_style": "COOL",
    
    # EMP-based
    "performance": "EMP",
    
    # WILL-based
    "endurance": "WILL", "resist_torture_drugs": "WILL",
}

# Дополняем из полных данных
for skill_name, skill_data in SKILLS_FULL.items():
    if skill_name not in SKILL_STAT and isinstance(skill_data, dict):
        SKILL_STAT[skill_name] = skill_data.get("stat", "COOL")


# ============================================================
# ОРУЖИЕ И БРОНЯ
# ============================================================

# Базовое оружие (будет дополнено из файлов)
WEAPONS = {
    "medium_pistol": {"name": "Средний пистолет", "damage": "2d6", "category": "pistol"},
    "heavy_pistol": {"name": "Тяжёлый пистолет", "damage": "3d6", "category": "pistol"},
    "shotgun": {"name": "Дробовик", "damage": "5d6", "category": "rifle"},
    "assault_rifle": {"name": "Штурмовая винтовка", "damage": "5d6", "category": "rifle"},
    "smg": {"name": "Пистолет-пулемёт", "damage": "3d6", "category": "rifle"},
    "sniper_rifle": {"name": "Снайперская винтовка", "damage": "5d6", "category": "rifle"},
    "knife": {"name": "Нож", "damage": "1d6", "category": "melee"},
    "bat": {"name": "Бита", "damage": "2d6", "category": "melee"},
    "machete": {"name": "Мачете", "damage": "2d6", "category": "melee"},
    "axe": {"name": "Топор", "damage": "3d6", "category": "melee"},
    "chainsaw": {"name": "Бензопила", "damage": "4d6", "category": "melee"},
    "grenade": {"name": "Граната", "damage": "6d6", "category": "explosive"},
}

# Дополняем из полных данных
for weapon_key, weapon_data in WEAPONS_FULL.items():
    if weapon_key not in WEAPONS and isinstance(weapon_data, dict):
        WEAPONS[weapon_key] = weapon_data


# Базовая броня
ARMOR = {
    "leathers": {"sp": 4},
    "kevlar": {"sp": 7},
    "light_armorjack": {"sp": 11},
    "metalgear": {"sp": 12},
    "medium_armorjack": {"sp": 12},
    "heavy_armorjack": {"sp": 14},
    "flak": {"sp": 15},
    "bodyplate": {"sp": 18},
}

# Дополняем из полных данных
for armor_key, armor_data in ARMOR_FULL.items():
    if armor_key not in ARMOR and isinstance(armor_data, dict):
        sp = armor_data.get("sp", 0)
        ARMOR[armor_key] = {"sp": sp}


# ============================================================
# СЛОЖНОСТЬ ПРОВЕРОК
# ============================================================

DV = {
    "simple": 9,
    "everyday": 13,
    "difficult": 15,
    "professional": 17,
    "heroic": 19,
    "incredible": 21,
    "legendary": 25,
}


# ============================================================
# ФУНКЦИИ БРОСКОВ
# ============================================================

def roll_dice(notation):
    """Бросает кубики по нотации, например '2d6'. Возвращает (сумма, список граней)."""
    if not notation or 'd' not in notation:
        return 0, []
    
    parts = notation.lower().split('d')
    count = int(parts[0]) if parts[0] else 1
    sides = int(parts[1]) if len(parts) > 1 and parts[1] else 6
    
    faces = [random.randint(1, sides) for _ in range(count)]
    return sum(faces), faces


def roll_d10(rng=None):
    """Бросает 1d10 с цепочкой (взрывные кубики).
    10 = бросай снова и добавляй, 1 = бросай снова и вычитай.
    Возвращает (первый_бросок, итог)."""
    rng = rng or random
    first = rng.randint(1, 10)
    total = first
    last = first
    while last in (10, 1):
        nxt = rng.randint(1, 10)
        if last == 10:
            total += nxt
        else:  # last == 1
            total -= nxt
        last = nxt
    return first, total


# ============================================================
# ФУНКЦИИ ПРОВЕРОК НАВЫКОВ
# ============================================================

def skill_check(stat, skill_level, dv, mods=0):
    """Стандартная проверка: 1d10 (с цепочкой) + stat + skill + mods против DV."""
    first_roll, chain_total = roll_d10()
    total = chain_total + stat + skill_level + mods
    
    # Криты определяются по первому броску (цепочка уже учла взрыв)
    critical = first_roll == 10
    fumble = first_roll == 1
    
    success = total >= dv
    margin = total - dv
    
    return {
        "dice": first_roll,
        "die_total": chain_total,
        "stat": stat,
        "skill": skill_level,
        "mods": mods,
        "total": total,
        "dv": dv,
        "success": success,
        "margin": margin,
        "critical": critical,
        "fumble": fumble,
    }


def resolve_assist(state, helper, dv, stat_key, skill_key):
    """Проверка помощи от другого персонажа."""
    stat = helper["stats"].get(stat_key, 2)
    skill = helper["skills"].get(skill_key, 0)
    mech = skill_check(stat, skill, dv)
    
    if mech["success"]:
        bonus = min(2, max(1, mech["margin"] // 3 + 1))
        return {"success": True, "bonus": bonus, "mechanics": mech}
    return {"success": False, "bonus": 0, "mechanics": mech}


# ============================================================
# ОСНОВНАЯ ФУНКЦИЯ ПРОВЕРКИ (ИНТЕГРАЦИЯ С РАНЕНИЯМИ)
# ============================================================

def resolve_check(state, actor, judge):
    """Обрабатывает действие игрока и возвращает механику результата."""
    
    # === FREE-ДЕЙСТВИЯ: без броска ===
    if judge.get("action_type") == "free":
        return {
            "dice": None, "die_total": None, "stat": None, "skill": None,
            "mods": 0, "total": None, "dv": None, "success": True,
            "margin": 0, "critical": False, "fumble": False,
            "actor": actor["name"], "action_type": "free",
            "skill": "", "stat_key": None, "dv_key": None, "no_roll": True,
        }
    
    # === ПОДГОТОВКА БРОСКА ===
    dv_key = judge.get("dv_key", "everyday")
    dv = judge.get("dv") or DV.get(dv_key, 13)
    skill = judge.get("skill") or ""
    stat_key = SKILL_STAT.get(skill, judge.get("stat", "COOL"))
    stat = actor["stats"].get(stat_key, 2)
    sk_lvl = actor["skills"].get(skill, 0)
    
    # Штраф за ранения из модульной системы
    wound_state = get_wound_state(actor.get("hp", actor.get("max_hp", 10)), 
                                   actor.get("max_hp", 10))
    mods = get_wound_penalty(wound_state)
    
    # === БРОСОК ===
    mech = skill_check(stat, sk_lvl, dv, mods)
    mech.update({
        "actor": actor["name"],
        "action_type": judge.get("action_type", "skill"),
        "skill": skill,
        "stat_key": stat_key,
        "dv_key": dv_key,
        "wound_state": wound_state,
        "wound_penalty": mods,
    })

    # === ОРУЖИЕ ПО УМОЛЧАНИЮ ===
    at = mech["action_type"]
    if at == "attack_ranged" and not judge.get("weapon"):
        judge["weapon"] = "heavy_pistol"
    if at == "attack_melee" and not judge.get("weapon"):
        judge["weapon"] = "knife"

    # === ТРАНСПОРТ: вождение и таран ===
    if at == "drive":
        vehicle_key = actor.get("vehicle")
        if not vehicle_key:
            mech.update({"drive_result": "no_vehicle",
                         "reason": "Персонаж не в транспорте"})
            return mech
        from . import vehicles as veh_mod
        v = veh_mod.get_vehicle(vehicle_key)
        mech.update({
            "drive_result": "maneuver",
            "vehicle": vehicle_key,
            "vehicle_name": (v or {}).get("name", vehicle_key),
        })

    if at == "ram":
        attacker_vehicle = actor.get("vehicle")
        if not attacker_vehicle:
            mech.update({"ram_result": "no_vehicle",
                         "reason": "Персонаж не в транспорте"})
            return mech
        from . import vehicles as veh_mod
        target_vehicle = (target or {}).get("vehicle")
        dmg = veh_mod.ram_damage(attacker_vehicle, target_vehicle or "car_compact")
        mech.update({
            "ram_result": "hit" if mech["success"] else "miss",
            "ram_raw": dmg["raw"],
            "ram_sp": dmg["sp"],
            "ram_net": dmg["net"] if mech["success"] else 0,
            "target": (target or {}).get("name"),
        })
        if target is not None and mech["success"] and dmg["net"] > 0:
            damage_result = apply_damage(target, dmg["net"])
            target["hp"] = damage_result["hp"]
            target["wound"] = damage_result["wound_state"]
            mech["target_hp"] = target["hp"]
            mech["target_wound"] = target["wound"]

    # === ПОИСК ЦЕЛИ ===
    target = None
    if judge.get("target"):
        target = next((n for n in state["npcs"] if n["id"] == judge.get("target")), None)
    
    if target is None and at in ("attack_ranged", "attack_melee"):
        low = (judge.get("_text") or "").lower()
        target = next((n for n in state["npcs"] if n["name"].lower() in low), None)
        if target is None:
            target = next((n for n in state["npcs"] if n["id"] == state.get("threat")), None)
        if target is None and state["npcs"]:
            target = state["npcs"][0]

    # Нетраннинг
    at = mech["action_type"]
    if at == "hack":
        # Проверяем, есть ли у персонажа Interface Plugs
        cyberware = actor.get("cyberware", [])
        has_interface = any("interface" in c.lower() for c in cyberware)
        
        if not has_interface:
            mech.update({
                "hack_result": "no_interface",
                "reason": "Нет Interface Plugs для входа в сеть",
            })
            return mech
        
        # Успешный вход в сеть
        if mech["success"]:
            arch_key = judge.get("architecture", "simple")
            net_state = netrunning.enter_architecture(actor, arch_key)
            
            if net_state["success"]:
                mech.update({
                    "hack_result": "entered",
                    "architecture": arch_key,
                    "floor": 1,
                    "max_floors": net_state["max_floors"],
                    "dv": net_state["dv"],
                })
            else:
                mech.update({
                    "hack_result": "failed",
                    "reason": net_state.get("reason", "Не удалось войти"),
                })
        else:
            mech.update({
                "hack_result": "failed_check",
                "reason": "Провал проверки interface",
            })

    # === ПРИМЕНЕНИЕ УРОНА ===
    if at in ("attack_ranged", "attack_melee") and mech["success"]:
        wkey = judge.get("weapon", "heavy_pistol" if at == "attack_ranged" else "knife")
        move_key = judge.get("move")  # приём боевого искусства (опционально)
        
        w = WEAPONS.get(wkey, {"damage": "2d6"})
        
        # Бросок урона
        dmg, faces = roll_dice(w.get("damage", "2d6"))
        sixes = sum(1 for f in faces if f == 6)
        crit = sixes >= 2
        
        # Защита брони
        sp = ARMOR.get((target or {}).get("armor", "leathers"), {}).get("sp", 0) if target else 0
        net = max(0, dmg - sp)
        
        # Бонус от приёма боевого искусства
        martial_effect = None
        martial_effect_desc = ""
        
        if move_key and move_key in martial.MOVES:
            net = martial.apply_move_bonus(move_key, net)
            martial_effect, martial_effect_desc = martial.get_move_effect(move_key)
        
        # Бонус за критический успех
        bonus = 5 if crit else 0
        total_damage = net + bonus
        
        mech.update({
            "weapon": wkey,
            "damage_roll": faces,
            "damage": dmg,
            "armor_sp": sp,
            "net_damage": net,
            "bonus_damage": bonus,
            "total_damage": total_damage,
            "target": (target or {}).get("name"),
            "critical_success": crit,
            "martial_move": move_key,
            "martial_effect": martial_effect,
            "martial_effect_desc": martial_effect_desc,
        })
        
        if target is not None:
            mech["target_id"] = target["id"]
            
            # Применяем урон через модульную систему
            if total_damage > 0:
                damage_result = apply_damage(target, total_damage, weapon_key=wkey)
                
                # Обновляем цель
                target["hp"] = damage_result["hp"]
                target["wound"] = damage_result["wound_state"]
                target["wound_penalty"] = damage_result["penalty"]
                
                # Критическая травма
                if damage_result["critical_injury"]:
                    mech["critical_injury"] = damage_result["critical_injury"]
                
                # Бросок смерти при смертельном ранении
                if damage_result["death_save"]:
                    death_result = death_save(target)
                    target["dead"] = death_result["dead"]
                    mech["death_save"] = death_result
                    if death_result["dead"]:
                        mech["target_dead"] = True
                
                # Эффект приёма боевого искусства
                if martial_effect == "sweep" and not target.get("dead"):
                    target["prone"] = True
                elif martial_effect == "disarm" and not target.get("dead"):
                    target["disarmed"] = True
                
                mech["target_hp"] = target["hp"]
                mech["target_wound"] = target["wound"]
    
    return mech


# ============================================================
# РЕАКЦИИ NPC
# ============================================================

def resolve_npc_reaction(st, actor, mech):
    """Все враждебные NPC реагируют на успешную атаку.
    
    Если атака успешна (даже если броня поглотила урон):
    - Цель атаки контратакует
    - Другие враждебные NPC в сцене могут присоединиться
    """
    if not mech.get("success") or mech.get("no_roll"):
        return None
    
    target_id = mech.get("target_id")
    if not target_id:
        return None
    
    # Находим цель атаки
    target = next((n for n in st["npcs"] if n["id"] == target_id), None)
    if not target or target.get("dead"):
        return None
    
    # Реакция цели атаки (обязательна)
    reaction = _generate_npc_attack(st, target, actor)
    if not reaction:
        return None
    
    # Ищем других NPC, которые могут присоединиться
    other_npcs = [n for n in st["npcs"] 
                  if n["id"] != target_id 
                  and not n.get("dead")
                  and _is_hostile(n)]
    
    if other_npcs:
        # Случайный другой NPC тоже атакует
        import random
        helper = random.choice(other_npcs)
        helper_attack = _generate_npc_attack(st, helper, actor)
        if helper_attack:
            reaction["helper"] = helper_attack
    
    return reaction


def _is_hostile(npc):
    """Проверяет, враждебен ли NPC."""
    name = npc.get("name", "").lower()
    hostile_keywords = ["охранник", "телохранитель", "стражник", "guard", "наёмник", "merc"]
    return any(k in name for k in hostile_keywords)


def _generate_npc_attack(st, npc, target_player):
    """Генерирует атаку NPC по игроку."""
    import random
    
    # Определяем оружие NPC
    weapon_key = "heavy_pistol"  # по умолчанию
    if "охранник" in npc.get("name", "").lower() or "телохранитель" in npc.get("name", "").lower():
        weapon_key = "heavy_pistol"
    elif "фиксер" in npc.get("name", "").lower():
        weapon_key = "medium_pistol"
    
    weapon = WEAPONS.get(weapon_key, {"damage": "2d6"})
    
    # Бросок атаки NPC
    stat = npc.get("stats", {}).get("REF", 4)
    skill = npc.get("skills", {}).get("handgun", 3)
    attack_roll = roll_dice("1d10")[0] + stat + skill
    target_dv = 13  # базовая сложность
    
    success = attack_roll >= target_dv
    
    result = {
        "npc": npc["name"],
        "success": success,
        "total": attack_roll,
        "dv": target_dv,
    }
    
    if success:
        # Бросок урона
        dmg, faces = roll_dice(weapon.get("damage", "2d6"))
        sp = ARMOR.get(target_player.get("armor", "leathers"), {}).get("sp", 0)
        net = max(0, dmg - sp)
        
        result.update({
            "damage": dmg,
            "armor_sp": sp,
            "net_damage": net,
            "weapon": weapon_key,
        })
        
        # Применяем урон к игроку
        if net > 0:
            damage_result = apply_damage(target_player, net, weapon_key=weapon_key)
            target_player["hp"] = damage_result["hp"]
            target_player["wound"] = damage_result["wound_state"]
            target_player["wound_penalty"] = damage_result["penalty"]
            
            if damage_result["critical_injury"]:
                result["critical_injury"] = damage_result["critical_injury"]
    
    return result

# ============================================================
# УТИЛИТЫ
# ============================================================

def get_enemy_template(enemy_id):
    """Возвращает шаблон врага из данных."""
    return ENEMIES_DATA.get("enemies", {}).get(enemy_id)


def get_faction(faction_name):
    """Возвращает данные фракции."""
    return FACTIONS_DATA.get("factions", {}).get(faction_name)


def get_martial_arts_style(style_name):
    """Возвращает стиль боевого искусства."""
    return MARTIAL_ARTS_DATA.get("styles", {}).get(style_name)
 
def _generate_npc_attack(st, npc, target_player):
    """Генерирует атаку NPC по игроку."""
    import random
    
    # Определяем оружие по имени
    weapon_key = "medium_pistol"
    name_lower = npc.get("name", "").lower()
    if "охранник" in name_lower or "телохранитель" in name_lower:
        weapon_key = "heavy_pistol"
    elif "фиксер" in name_lower:
        weapon_key = "medium_pistol"
    
    weapon = WEAPONS.get(weapon_key, {"damage": "2d6", "skill": "handgun"})
    
    # Бросок атаки
    stat = npc.get("stats", {}).get("REF", 4)
    skill = npc.get("skills", {}).get("handgun", 3)
    roll, faces = roll_dice("1d10")
    attack_total = roll + stat + skill
    dv = 13
    
    success = attack_total >= dv
    
    result = {
        "npc": npc["name"],
        "success": success,
        "total": attack_total,
        "dv": dv,
        "weapon": weapon_key,
    }
    
    if success:
        # Бросок урона
        dmg, dmg_faces = roll_dice(weapon.get("damage", "2d6"))
        sp = ARMOR.get(target_player.get("armor", "leathers"), {}).get("sp", 0)
        net = max(0, dmg - sp)
        
        result.update({
            "damage": dmg,
            "armor_sp": sp,
            "net_damage": net,
        })
        
        # Применяем урон к игроку
        if net > 0:
            damage_result = apply_damage(target_player, net, weapon_key=weapon_key)
            target_player["hp"] = damage_result["hp"]
            target_player["wound"] = damage_result["wound_state"]
            target_player["wound_penalty"] = damage_result["penalty"]
            
            if damage_result.get("critical_injury"):
                result["critical_injury"] = damage_result["critical_injury"]
    
    return result    
 
 # Алиас для обратной совместимости со старыми тестами
wound_state = get_wound_state   
        