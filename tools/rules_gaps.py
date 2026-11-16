"""Формирует REVIEW_GAPS.json: только незакрытые ключи + конфликты + подсказки,
где искать в книге. Первый проход захлебнулся на 29 ключах сразу — тут узко."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from backend import creation, engine, rules

ROOT = pathlib.Path(__file__).resolve().parents[1]

HINTS = {
    "stat_pool_edgerunner": "Character Creation, методы Streetrat / Edgerunner / Complete Package",
    "skill_pool_edgerunner": "Character Creation, шаг распределения Skill Points",
    "skill_list": "Skills chapter, таблица навыков с привязкой к STAT",
    "stat_list": "Character Creation, блок STAT",
    "roles": "Roles chapter, перечень ролей",
    "starting_eb": "Character Creation / Gear, стартовые средства по методу и роли",
    "range_dv": "Combat, таблица DV по дистанциям для типов оружия",
    "aimed_shot_penalties": "Combat, Aimed Shot (голова / конечность)",
    "aimed_shot_multipliers": "Combat, урон при попадании в голову / конечность",
    "armor_ablation": "Armor / Combat, Ablation — на сколько падает SP и при каком условии",
    "critical_injury_trigger": "Combat, Critical Injury — сколько шестёрок на кубиках урона",
    "critical_injury_bonus": "Combat, бонусный урон при критической травме",
    "critical_injury_table": "Trauma Team / Critical Injury tables",
    "wound_states": "Combat, Wound States — пороги HP",
    "wound_penalties": "Combat, штрафы за Wound States",
    "death_save_formula": "Combat, Death Save",
    "initiative_formula": "Combat, Initiative / порядок хода",
    "autofire_rules": "Weapons / Combat, Autofire",
    "rof_rules": "Weapons, что означает ROF за действие",
    "melee_opposed_by": "Combat, Melee attack — чем защищается цель",
    "ranged_defense": "Combat, Ranged attack — DV или встречный бросок",
    "humanity_loss_rules": "Cyberware, Humanity Loss",
    "interface_dv": "Netrunning, Interface / вход в архитектуру",
    "architectures": "Netrunning, NET Architecture",
    "program_list": "Netrunning, Programs",
    "black_ice": "Netrunning, Black ICE",
}

WEAPON_GAPS = ["grenade", "flamethrower"]


def build():
    gaps = []
    for pack in ["creation", "combat", "armor", "weapons", "cyberware", "netrunning", "gear"]:
        for key, rec in rules.load(pack)["entries"].items():
            if rec.get("verified"):
                continue
            gaps.append({
                "pack": pack, "key": key,
                "current_value": rec.get("value"),
                "note": rec.get("note", ""),
                "where_to_look": HINTS.get(key, ""),
            })

    weapon_requests = [
        {"pack": "weapons", "key": f"table.{k}",
         "code_value": engine.WEAPONS.get(k),
         "task": "Отдельная строка книги для этого оружия (damage, rof, mag, skill, conceal, price). "
                 "НЕ приравнивать ручную гранату к гранатомёту."}
        for k in WEAPON_GAPS if k in engine.WEAPONS
    ]

    conflicts = [{
        "key": "creation.stat_pool_edgerunner",
        "claims": [
            {"value": "template roll (no fixed pool)", "page": 78},
            {"value": 62, "page": 79, "quote": "Starting Character 62"},
        ],
        "code_value": creation.limits()["stat_pool"],
        "resolution_needed": "Выписать отдельно для Streetrat / Edgerunner / Complete Package: "
                             "пул STAT и пул Skill, числом или null. Без прозы.",
        "extra_keys": ["stat_pool_streetrat", "stat_pool_complete_package",
                       "skill_pool_streetrat", "skill_pool_complete_package"],
    }]

    return {
        "book": "Cyberpunk RED Core Rulebook",
        "pass": 2,
        "rules_status": rules.status(),
        "gaps": gaps,
        "weapon_requests": weapon_requests,
        "conflicts": conflicts,
        "output_schema": {
            "entries": [{"pack": "...", "key": "...", "value": "...",
                         "page": "<int>", "quote": "<=200 символов, содержит значение>",
                         "confidence": "high|medium|low"}],
            "not_found": [{"pack": "...", "key": "...", "reason": "..."}],
        },
        "hard_rules": [
            "Только JSON, без прозы",
            "page обязателен, quote дословная и содержит значение",
            "Нет в книге — писать в not_found, не выдумывать",
            "Числовые пулы — числами, не строками",
            "Большие таблицы можно дробить на ключи с суффиксами, у каждого своя страница",
        ],
    }


if __name__ == "__main__":
    payload = build()
    dest = ROOT / "REVIEW_GAPS.json"
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"REVIEW_GAPS.json: {len(payload['gaps'])} незакрытых ключей, "
          f"{len(payload['weapon_requests'])} оружий, {len(payload['conflicts'])} конфликт")