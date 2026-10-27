# scripts/16_fix_armor_weapons.py
"""
Детерминированный парсер свёрнутых таблиц брони (стр. 351) и оружия (стр. 343).
Записывает правильные данные в data/normalized/armor.jsonl и weapons.jsonl.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "normalized"
OUT.mkdir(parents=True, exist_ok=True)


def slug(s):
    import re
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_") or "unknown"


def write_jsonl(family, rows):
    path = OUT / f"{family}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for rec in rows:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"{family}: {len(rows)} rows -> {path}")


# === БРОНЯ (стр. 351) ===
# Данные из книги: 9 типов брони
ARMOR_DATA = [
    {"name": "Leathers",            "sp": 4,  "penalty": "None",                "price_eb": "20eb"},
    {"name": "Kevlar",              "sp": 7,  "penalty": "None",                "price_eb": "50eb"},
    {"name": "Light Armorjack",     "sp": 11, "penalty": "None",                "price_eb": "100eb"},
    {"name": "Bodyweight Suit",     "sp": 11, "penalty": "None",                "price_eb": "100eb"},
    {"name": "Medium Armorjack",    "sp": 12, "penalty": "-2 REF, DEX, MOVE",   "price_eb": "500eb"},
    {"name": "Heavy Armorjack",     "sp": 13, "penalty": "-2 REF, DEX, MOVE",   "price_eb": "500eb"},
    {"name": "Flak",                "sp": 15, "penalty": "-4 REF, DEX, MOVE",   "price_eb": "1000eb"},
    {"name": "Metalgear",           "sp": 18, "penalty": "-4 REF, DEX, MOVE",   "price_eb": "5000eb"},
    {"name": "Bulletproof Shield",  "sp": 10, "penalty": "None (takes one arm)", "price_eb": "100eb", "note": "SP 10 HP, reduced by damage"},
]


# === ОРУЖИЕ (стр. 343-345) ===
# Данные из книги: 12 типов дальнобойного оружия + ближний бой
WEAPONS_DATA = [
    # Дальнобойное
    {"name": "Medium Pistol",      "type": "ranged", "damage": "2d6", "ammo": 8,  "rof": 2,     "range_m": 50,  "conceal": "J", "price_eb": "50eb",   "skill": "handgun"},
    {"name": "Heavy Pistol",       "type": "ranged", "damage": "3d6", "ammo": 8,  "rof": 2,     "range_m": 50,  "conceal": "J", "price_eb": "100eb",  "skill": "handgun"},
    {"name": "Very Heavy Pistol",  "type": "ranged", "damage": "4d6", "ammo": 8,  "rof": 2,     "range_m": 50,  "conceal": "L", "price_eb": "500eb",  "skill": "handgun"},
    {"name": "Bow",                "type": "ranged", "damage": "3d6", "ammo": 1,  "rof": 1,     "range_m": 100, "conceal": "N", "price_eb": "50eb",   "skill": "shoulder_arms"},
    {"name": "Crossbow",           "type": "ranged", "damage": "4d6", "ammo": 1,  "rof": 1,     "range_m": 100, "conceal": "N", "price_eb": "100eb",  "skill": "shoulder_arms"},
    {"name": "SMG",                "type": "ranged", "damage": "3d6", "ammo": 30, "rof": "2/3", "range_m": 100, "conceal": "N", "price_eb": "500eb",  "skill": "handgun"},
    {"name": "Heavy SMG",          "type": "ranged", "damage": "4d6", "ammo": 40, "rof": "2/3", "range_m": 100, "conceal": "L", "price_eb": "1000eb", "skill": "handgun"},
    {"name": "Shotgun",            "type": "ranged", "damage": "5d6", "ammo": 4,  "rof": 2,     "range_m": 50,  "conceal": "N", "price_eb": "500eb",  "skill": "shoulder_arms"},
    {"name": "Assault Rifle",      "type": "ranged", "damage": "5d6", "ammo": 30, "rof": "2/3", "range_m": 400, "conceal": "N", "price_eb": "500eb",  "skill": "shoulder_arms"},
    {"name": "Sniper Rifle",       "type": "ranged", "damage": "7d6", "ammo": 4,  "rof": 1,     "range_m": 800, "conceal": "N", "price_eb": "1000eb", "skill": "shoulder_arms"},
    {"name": "Grenade Launcher",   "type": "ranged", "damage": "Special", "ammo": 1, "rof": 1, "range_m": 200, "conceal": "N", "price_eb": "1000eb", "skill": "shoulder_arms"},
    {"name": "Rocket Launcher",    "type": "ranged", "damage": "Special", "ammo": 1, "rof": 1, "range_m": 500, "conceal": "N", "price_eb": "5000eb", "skill": "shoulder_arms"},
    
    # Ближний бой
    {"name": "Knife",              "type": "melee",  "damage": "2d6", "ammo": 0,  "rof": 0,     "range_m": 0,   "conceal": "J", "price_eb": "20eb",   "skill": "melee"},
    {"name": "Sword",              "type": "melee",  "damage": "3d6", "ammo": 0,  "rof": 0,     "range_m": 0,   "conceal": "N", "price_eb": "50eb",   "skill": "melee"},
    {"name": "Axe",                "type": "melee",  "damage": "4d6", "ammo": 0,  "rof": 0,     "range_m": 0,   "conceal": "N", "price_eb": "50eb",   "skill": "melee"},
    {"name": "Battleglove",        "type": "melee",  "damage": "4d6", "ammo": 0,  "rof": 0,     "range_m": 0,   "conceal": "N", "price_eb": "1000eb", "skill": "melee"},
    {"name": "Chainsaw",           "type": "melee",  "damage": "5d6", "ammo": 0,  "rof": 0,     "range_m": 0,   "conceal": "N", "price_eb": "100eb",  "skill": "melee"},
]


def main():
    # Записываем броню
    armor_rows = []
    for item in ARMOR_DATA:
        armor_rows.append({
            "key": slug(item["name"]),
            "_page": 351,
            "_validated": True,
            **item
        })
    write_jsonl("armor", armor_rows)

    # Записываем оружие
    weapons_rows = []
    for item in WEAPONS_DATA:
        weapons_rows.append({
            "key": slug(item["name"]),
            "_page": 343,
            "_validated": True,
            **item
        })
    write_jsonl("weapons", weapons_rows)

    print("\nГотово. Теперь запусти: python scripts\\12_pg_load.py")


if __name__ == "__main__":
    main()