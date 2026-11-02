# 10_play.py
import requests

API = "http://localhost:8000"

SCENARIO = {
    "scene": ("Бар 'Ржавый болт', Ночной Город, 23:40. За угловым столом среди дыма "
              "и неоновых бликов сидит фиксер Кесслер и ждёт тебя. На столе — стакан "
              "синтетического виски и дата-планшет с контрактом."),
    "heat": 1,
    "clocks": {},
    "npcs": [
        {"id": "kessler", "name": "Фиксер Кесслер", "hp": 15, "max_hp": 15,
         "wound": "unharmed", "armor": "leathers"}
    ],
}

CAREER_SKILLS = {
    "Rockerboy": ["performance", "persuasion", "human_perception", "acting"],
    "Solo": ["handgun", "melee_weapon", "evasion", "athletics"],
    "Netrunner": ["interface", "programming", "electronics_security_tech", "perception"],
    "Tech": ["basic_tech", "electronics_security_tech", "cybertech", "weaponstech"],
    "Medtech": ["paramedic", "first_aid", "pharmaceuticals", "human_perception"],
    "Media": ["deduction", "library_search", "persuasion", "education"],
    "Lawman": ["handgun", "perception", "deduction", "criminology"],
    "Exec": ["persuasion", "conversation", "deduction", "trading"],
    "Nomad": ["drive_land_vehicle", "land_vehicle_tech", "endurance", "perception"],
    "Fixer": ["streetwise", "persuasion", "conversation", "trading"],
}

ALL_SKILLS = [
    # INT (16)
    "accounting", "conceal_reveal_object", "criminology", "cryptography",
    "deduction", "education", "gamble", "language", "library_search",
    "lip_reading", "local_expert", "perception", "science", "tactics",
    "tracking", "wilderness_survival",
    # REF (15)
    "brawling", "contortionist", "dance", "drive_land_vehicle",
    "drive_sea_vehicle", "evasion", "handgun", "heavy_weapons",
    "martial_arts", "melee_weapon", "pilot_air_vehicle",
    "pilot_sea_vehicle", "riding", "shoulder_arms", "stealth",
    # TECH (15)
    "air_vehicle_tech", "basic_tech", "cybertech", "demolitions",
    "electronics_security_tech", "first_aid", "forgery",
    "land_vehicle_tech", "paint_draw_photography", "paramedic",
    "pharmaceuticals", "pick_lock", "pick_pocket", "sea_vehicle_tech",
    "weaponstech",
    # COOL (10)
    "acting", "bribery", "conversation", "human_perception",
    "interrogation", "persuasion", "personal_grooming", "streetwise",
    "trading", "wardrobe_style",
    # EMP (1)
    "performance",
    # WILL (3)
    "concentration", "endurance", "resist_torture_drugs",
    # BODY (1)
    "athletics",
    # MOVE (1)
    "stealth_move",
    # Netrunner (2)
    "interface", "programming",
]

LIFEPATH_TABLES = {
    "cultural_origins": ["North American", "South American", "Western European",
                         "Eastern European", "Middle Eastern", "North African",
                         "Sub-Saharan African", "South Asian", "Southeast Asian",
                         "East Asian", "Oceania/Pacific"],
    "family_background": ["Corporate Elite", "Corporate Manager", "Corporate Worker",
                          "Nomad Clan", "Gang family", "Urban Homeless",
                          "Rural Family Farm", "Military family", "Law Enforcement family",
                          "Entertainment family", "Criminal family"],
    "childhood_environment": ["The Street", "War Zone", "Nomad pack",
                              "Gang-controlled district", "Urban slums", "Suburban sprawl",
                              "Corporate housing block", "Rural wasteland",
                              "Space station / orbital", "Secure corporate arcology",
                              "Military base"],
    "family_crisis": ["Family destroyed by war", "Family imprisoned", "Family bankrupt",
                      "Family killed by gang", "Family member killed by corporation",
                      "Family split apart", "Family member went missing",
                      "Family member betrayed you", "Family member became cyberpsycho",
                      "Family exiled you", "No crisis — stable childhood"],
}


# ============ СОЗДАНИЕ ПЕРСОНАЖА ============

def choose_role():
    print("\n=== ВЫБОР РОЛИ ===")
    roles = list(CAREER_SKILLS.keys())
    for i, r in enumerate(roles, 1):
        print(f"  {i}. {r}")
    while True:
        s = input("Введи номер (1-10): ").strip()
        if s.isdigit() and 1 <= int(s) <= len(roles):
            return roles[int(s) - 1]
        print("Неверный номер")


def distribute_stats():
    print("\n=== РАСПРЕДЕЛЕНИЕ СТАТОВ (62 очка, каждая 2..8) ===")
    stats_list = ["INT", "REF", "DEX", "TECH", "COOL", "WILL", "LUCK", "MOVE", "BODY", "EMP"]
    while True:
        stats = {}
        for s in stats_list:
            while True:
                raw = input(f"  {s} (2..8): ").strip()
                if raw.isdigit() and 2 <= int(raw) <= 8:
                    stats[s] = int(raw)
                    break
                print("    Введи число от 2 до 8")
        total = sum(stats.values())
        if total == 62:
            return stats
        print(f"\nСумма {total}, нужно 62. Начнём заново.\n")


def choose_lifepath():
    print("\n=== ПРЕДЫСТОРИЯ ===")
    while True:
        s = input("Создать самому (1) или кинуть 2d6 (2)? ").strip()
        if s in ("1", "2"):
            break
    mode = "manual" if s == "1" else "roll"
    import random as _rnd
    lifepath = {}
    for key, options in LIFEPATH_TABLES.items():
        if mode == "roll":
            d1, d2 = _rnd.randint(1, 6), _rnd.randint(1, 6)
            idx = min(d1 + d2 - 2, len(options) - 1)
            lifepath[key] = options[idx]
            print(f"  {key}: брошено {d1}+{d2}={d1+d2} -> {options[idx]}")
        else:
            print(f"  {key}:")
            for i, o in enumerate(options, 1):
                print(f"    {i}. {o}")
            while True:
                s2 = input("  Выбор: ").strip()
                if s2.isdigit() and 1 <= int(s2) <= len(options):
                    lifepath[key] = options[int(s2) - 1]
                    break
                print("    Неверный номер")
    return lifepath


def distribute_skills(career_skills):
    print("\n=== РАСПРЕДЕЛЕНИЕ НАВЫКОВ ===")
    print("Карьерные навыки (старт 2-3 каждый):")
    skills = {}
    for sk in career_skills:
        while True:
            s = input(f"  {sk} (2 или 3): ").strip()
            if s in ("2", "3"):
                skills[sk] = int(s)
                break
    pickup_available = [s for s in ALL_SKILLS if s not in career_skills]
    print("\nДополнительные навыки (10 очков, максимум 6 на навык):")
    print("Формат: <навык> <ранк>. Пустая строка — завершить.")
    print("Доступные навыки (не карьерные):")
    for i in range(0, len(pickup_available), 6):
        print("  " + ", ".join(pickup_available[i:i+6]))
    pool = 10
    while pool > 0:
        raw = input(f"  [осталось {pool}] > ").strip().lower()
        if not raw:
            break
        parts = raw.split()
        if len(parts) != 2 or not parts[1].isdigit():
            print("    Формат: <навык> <ранк>")
            continue
        sk, rank = parts[0], int(parts[1])
        if rank < 1 or rank > 6:
            print("    Ранк 1..6")
            continue
        if rank > pool:
            print(f"    Не хватает очков (осталось {pool})")
            continue
        if sk in career_skills:
            print(f"    Навык {sk} уже карьерный (ранк {skills[sk]}) — pickup его не дублирует")
            continue
        current = skills.get(sk, 0)
        if current + rank > 6:
            print(f"    Превышен максимум (было {current}, +{rank} = {current + rank})")
            continue
        skills[sk] = current + rank
        pool -= rank
    return skills


def interactive_chargen():
    print("\n" + "=" * 70)
    print("   СОЗДАНИЕ ПЕРСОНАЖА (по правилам Cyberpunk RED)")
    print("=" * 70)
    role = choose_role()
    career = CAREER_SKILLS[role]
    print(f"\nРоль: {role} | Карьерные навыки: {', '.join(career)}")
    stats = distribute_stats()
    lifepath = choose_lifepath()
    skills = distribute_skills(career)
    name = input("\nИмя/хэндл: ").strip() or "Чоум"
    style = input("Визуальная деталь (или Enter): ").strip()
    ch = {
        "name": name, "role": role, "stats": stats, "skills": skills,
        "hp": stats["BODY"] * 2, "max_hp": stats["BODY"] * 2,
        "wound": "unharmed", "dsp": 0, "dead": False,
        "humanity": stats["EMP"] * 10, "lifepath": lifepath,
    }
    if style:
        ch["style"] = style
    resp = requests.post(f"{API}/chargen/validate", json=ch, timeout=10)
    v = resp.json()
    if not v["valid"]:
        print(f"\n[ошибка] Проблемы валидации: {v['problems']}")
        return None
    return ch


def make_players(mode="interactive"):
    players = []
    for i in range(2):
        if mode == "random":
            players.append(requests.post(f"{API}/chargen",
                                         json={"mode": "random"}, timeout=30).json())
            continue
        print(f"\n--- ИГРОК {i+1} ---")
        ch = interactive_chargen()
        if ch is None:
            print("Откат на random для этого игрока...")
            ch = requests.post(f"{API}/chargen",
                               json={"mode": "random"}, timeout=30).json()
        players.append(ch)
    return players


# ============ ОТОБРАЖЕНИЕ ============

def show_state(st):
    print("=" * 70)
    act = st.get("act", "fixer")
    print(f"АКТ: {act.upper()} | HEAT {st['heat']}")
    if act == "fixer":
        print(f"Patience: {st.get('patience', 4)} | Раунд: {st.get('fixer_round', 0)}")
    elif act == "recon":
        print(f"Слоты времени: {st.get('recon_slots', 0)} | Assets: {st.get('assets', [])}")
    elif act == "infiltration":
        print(f"Suspicion: {st.get('suspicion', 0)} | Lockdown: {st.get('lockdown', 0)}/6")
    print(f"Контракт: {st.get('contract', {})}")
    if st.get("revealed_beats"):
        print(f"  Раскрыто: {len(st['revealed_beats'])}/5 битов контракта")
    if st.get("granted"):
        print(f"  На руках: {', '.join(st['granted'])}")
    for p in st["players"]:
        print(f"  {p['name']} [{p['role']}] HP {p['hp']}/{p['max_hp']} {p.get('wound', '')}")
    for n in st.get("npcs", []):
        print(f"  NPC {n['name']}: HP {n['hp']}/{n['max_hp']} {n.get('wound', '')}")
    print(f"Ходит: {st['order'][st['turn']]}")


def show_result(r, sid):
    m = r.get("mechanics", {})
    if m.get("no_roll"):
        line = f"[без броска] свободное действие: {m.get('actor', '')}"
    else:
        line = (f"[механика] {m.get('action_type', '?')} | "
                f"{m.get('stat_key', '?')}+{m.get('skill', '?')}: "
                f"{m.get('total')} vs DV{m.get('dv')} ({m.get('dv_key', '?')}) -> "
                + ("УСПЕХ" if m.get("success") else "ПРОВАЛ"))
        if m.get("damage") is not None:
            line += (f" | цель {m.get('target')}: урон {m.get('damage')} "
                     f"- SP{m.get('armor_sp')} = {m.get('net_damage')}")
        if m.get("critical_injury"):
            line += " | КРИТ-ТРАВМА"
    nr = m.get("npc_reaction")
    if nr:
        line += (f"\n[ответ NPC] {nr['npc']}: "
                 + ("попадание" if nr["success"] else "промах")
                 + f", урон по игроку {nr.get('net_damage', 0)}")
    print("\n" + line + "\n")
    print(r.get("narration") or "(нарратив недоступен)")
    for q in r.get("questions", []):
        print("  ?", q)
    if r.get("choices"):
        print("  варианты:", " / ".join(r["choices"]))
    print()

    tid = r.get("turn_id")
    if not tid:
        return
    rate = input("Оценка нарратива (1-5) / Enter = пропустить: ").strip()
    if not rate.isdigit() or not 1 <= int(rate) <= 5:
        return
    edited = None
    if int(rate) <= 3:
        edited = input("Твой вариант нарратива / Enter = пропустить: ").strip() or None
    try:
        requests.post(f"{API}/session/{sid}/turn/{tid}/rate",
                      json={"rating": int(rate), "edited": edited}, timeout=10)
        print("Оценка сохранена.\n")
    except Exception as e:
        print(f"Не удалось сохранить оценку: {e}")


# ============ ГЛАВНЫЙ ЦИКЛ ============

def main():
    print("   CYBERPUNK RED — текстовая настолка с ИИ")
    print("   ======================================\n")
    while True:
        m = input("Создание персонажа: интерактивно (1) / случайные (2)? ").strip()
        if m in ("1", "2"):
            break
    mode = "interactive" if m == "1" else "random"

    players = make_players(mode=mode)
    s = requests.post(f"{API}/session",
                      json={"players": players, "scenario": SCENARIO}, timeout=60).json()
    sid = s["id"]
    print("\nсессия:", sid)
    print("команды: текст = действие | assist:Имя текст = Имя помогает текущему")
    print("пример: assist:Никс взламываю замок прилавка\n")

    while True:
        st = requests.get(f"{API}/session/{sid}", timeout=30).json()
        show_state(st)
        actor = st["order"][st["turn"]]
        raw = input(f"{actor}> ").strip()
        if not raw:
            continue
        if raw.lower().startswith("assist:"):
            rest = raw.split(":", 1)[1].strip()
            parts = rest.split(" ", 1)
            helper = parts[0]
            text = parts[1] if len(parts) > 1 else ""
            payload = {"player": actor, "text": text, "assist": helper}
        else:
            payload = {"player": actor, "text": raw}
        try:
            r = requests.post(f"{API}/session/{sid}/action",
                              json=payload, timeout=300).json()
        except Exception as e:
            print("[ошибка запроса]", e)
            continue
        show_result(r, sid)


if __name__ == "__main__":
    main()