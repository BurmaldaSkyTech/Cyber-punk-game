# backend/scenario.py
"""Трёхактный сценарий: Фиксер → Рекогносцировка → Проникновение."""
import random

ACTS = ["fixer", "recon", "infiltration"]

SCENARIO_META = {
    "name": "Контракт: Лазарь",
    "client": "Фиксер Кесслер",
    "objective": "Извлечь нейроимплант 'Лазарь' из дата-узла Biotechnica",
    "pay_base": 2000,
}

# === АКТ 1: ФИКСЕР ===

FIXER_TRADE_OPTIONS = [
    {"id": "pay_bonus", "label": "+1000eb к выплате", "effect": {"pay_delta": 1000}},
    {"id": "advance", "label": "Аванс 500eb", "effect": {"advance": 500}},
    {"id": "gear_jammer", "label": "Глушилка камер (30 сек)", "effect": {"gear": "cam_jammer"}},
    {"id": "gear_fake_pass", "label": "Фальшивый пропуск Biotechnica", "effect": {"gear": "fake_pass"}},
    {"id": "gear_medkit", "label": "Мед-аптечка (paramedic +2)", "effect": {"gear": "medkit"}},
    {"id": "intel_patrol", "label": "Интел: расписание патрулей", "effect": {"intel": "patrol_schedule"}},
    {"id": "intel_blindspot", "label": "Интел: слепая зона камер", "effect": {"intel": "blind_spot"}},
    {"id": "heat_reduce", "label": "Старт suspicion -1", "effect": {"suspicion_start": -1}},
]

FIXER_DV_SCALING = [13, 15, 17]  # DV для раундов 1, 2, 3

# === АКТ 2: РЕКОГНОСЦИРОВКА ===

RECON_CHECKS = [
    {"id": "blind_spot", "skill": "perception", "stat": "INT", "dv": 13,
     "desc": "Осмотреть территорию на слепые зоны камер"},
    {"id": "patrol_schedule", "skill": "deduction", "stat": "INT", "dv": 15,
     "desc": "Вычислить расписание патрулей по следам и мусору"},
    {"id": "inside_contact", "skill": "streetwise", "stat": "INT", "dv": 15,
     "desc": "Найти уборщика, который откроет служебную дверь"},
    {"id": "cam_loop", "skill": "interface", "stat": "INT", "dv": 17,
     "desc": "Взломать камеры: петли по 30 секунд"},
    {"id": "code_lock", "skill": "basic_tech", "stat": "TECH", "dv": 15,
     "desc": "Подобрать код служебного входа"},
]

RECON_TIME_SLOTS = 3  # 3 проверки максимум

# === АКТ 3: ПРОНИКНОВЕНИЕ ===

GUARD_STATS = {"REF": 5, "DEX": 4, "BODY": 5}
GUARD_SKILLS = {"handgun": 3, "perception": 3}
GUARD_WEAPON = "heavy_pistol"
GUARD_ARMOR = "kevlar"

SERGEANT_STATS = {"REF": 6, "DEX": 5, "BODY": 7}
SERGEANT_SKILLS = {"shoulder_arms": 4, "perception": 4}
SERGEANT_WEAPON = "shotgun"
SERGEANT_ARMOR = "heavy_armorjack"

INFILTRATION_OBJECTIVE = "Крио-капсула с имплантом 'Лазарь'"

# Пути проникновения
INFILTRATION_PATHS = {
    "stealth": {
        "name": "Скрытный путь",
        "skill": "stealth", "stat": "DEX",
        "base_dv": 15,
        "modifiers": {
            "blind_spot": -4, "patrol_schedule": -2,
            "cam_jammer": -3, "cam_loop": -2
        }
    },
    "tech": {
        "name": "Технический путь",
        "skill": "electronics", "stat": "TECH",
        "base_dv": 15,
        "modifiers": {"code_lock": -4, "cam_loop": -3}
    },
    "social": {
        "name": "Социальный путь",
        "skill": "persuasion", "stat": "EMP",
        "base_dv": 17,
        "modifiers": {"fake_pass": -6, "inside_contact": -3}
    },
    "assault": {
        "name": "Штурм (опасно)",
        "skill": "handgun", "stat": "REF",
        "base_dv": 13,
        "modifiers": {},
        "suspicion_on_fail": 3
    }
}

EXTRACTION_DV = 15  # paramedic check
EXTRACTION_MODIFIER = {"medkit": -2}  # с аптечкой легче


def get_act(st):
    """Возвращает текущий акт из state."""
    return st.get("act", "fixer")


def advance_act(st):
    """Переход к следующему акту."""
    current = st.get("act", "fixer")
    if current == "fixer":
        st["act"] = "recon"
        st["recon_slots"] = RECON_TIME_SLOTS
        st["assets"] = []
    elif current == "recon":
        st["act"] = "infiltration"
        st["suspicion"] = st.get("suspicion", 0)
        st["lockdown"] = 0
    else:
        st["act"] = "complete"


def init_scenario():
    """Начальное состояние сценария."""
    return {
        "act": "fixer",
        "contract": {"pay": SCENARIO_META["pay_base"], "advance": 0, "gear": [], "intel": []},
        "fixer_round": 0,
        "patience": 4,
        "recon_slots": 0,
        "assets": [],
        "suspicion": 0,
        "lockdown": 0,
    }


def fixer_trade(st, action_text):
    """Обработка раунда торга с фиксером."""
    round_num = st.get("fixer_round", 0)
    if round_num >= 3:
        return {"success": False, "reason": "Торг окончен", "next": "advance_act"}
    
    dv = FIXER_DV_SCALING[min(round_num, len(FIXER_DV_SCALING)-1)]
    return {
        "action_type": "social",
        "skill": "persuasion",
        "stat_key": "EMP",
        "dv_key": None,
        "dv": dv,
        "query": "social opposed check persuasion"
    }


def fixer_resolve(st, success):
    """Результат раунда торга."""
    if success:
        return {
            "success": True,
            "message": "Выбери одно улучшение контракта",
            "options": FIXER_TRADE_OPTIONS
        }
    else:
        st["patience"] = st.get("patience", 4) - 1
        if st["patience"] <= 0:
            return {"success": False, "message": "Кесслер теряет терпение, фиксирует базовые условия", "next": "advance_act"}
        return {"success": False, "message": f"Кесслер недоволен (patience: {st['patience']})"}


def recon_check(st, check_id):
    """Проверка рекогносцировки."""
    check = next((c for c in RECON_CHECKS if c["id"] == check_id), None)
    if not check:
        return {"error": "Неизвестная проверка"}
    
    if st.get("recon_slots", 0) <= 0:
        return {"error": "Время вышло"}
    
    st["recon_slots"] -= 1
    return {
        "action_type": "skill",
        "skill": check["skill"],
        "stat_key": check["stat"],
        "dv_key": None,
        "dv": check["dv"],
        "query": f"{check['skill']} check"
    }


def recon_resolve(st, check_id, success):
    """Результат проверки рекогносцировки."""
    if success:
        if check_id not in st.get("assets", []):
            st["assets"].append(check_id)
        return {"success": True, "message": f"Asset получен: {check_id}"}
    else:
        st["suspicion"] = st.get("suspicion", 0) + 1
        return {"success": False, "message": f"Suspicion +1 (теперь {st['suspicion']})"}


def infiltration_path(st, path_id):
    """Расчёт DV для пути проникновения."""
    path = INFILTRATION_PATHS.get(path_id)
    if not path:
        return {"error": "Неизвестный путь"}
    
    dv = path["base_dv"]
    for asset, mod in path["modifiers"].items():
        if asset in st.get("assets", []):
            dv += mod
    
    return {
        "action_type": "skill",
        "skill": path["skill"],
        "stat_key": path["stat"],
        "dv_key": None,
        "dv": dv,
        "query": f"{path['skill']} check infiltration"
    }


def extraction_check(st):
    """Проверка извлечения импланта."""
    dv = EXTRACTION_DV
    for asset, mod in EXTRACTION_MODIFIER.items():
        if asset in st.get("assets", []):
            dv += mod
    
    return {
        "action_type": "skill",
        "skill": "paramedic",
        "stat_key": "INT",
        "dv_key": None,
        "dv": dv,
        "query": "paramedic check extraction"
    }