# 10_play.py
import requests
import json

API = "http://localhost:8000"


# ============ КОНФИГ ============

SCENARIO = {
    "scene": ("Ржавый рынок, Ночной Город, 02:14. Под эстакадой гудит чёрный рынок: "
              "краденые импланты, дроны, синтетическая лапша. Где-то между рядами прячется "
              "курьер с нейрофлешкой, которую хочет получить фиксер Кесслер."),
    "heat": 1,
    "clocks": {"security_response": {"max": 6, "progress": 1}},
    "npcs": [
        {"id": "courier", "name": "Курьер", "hp": 20, "max_hp": 20,
         "wound": "unharmed", "armor": "leathers"},
        {"id": "guard1", "name": "Охранник рынка", "hp": 24, "max_hp": 24,
         "wound": "unharmed", "armor": "kevlar"}
    ]
}


# ============ СОЗДАНИЕ ПЕРСОНАЖА ============

def choose_role():
    print("\n=== ВЫБОР РОЛИ ===")
    roles = ["Rockerboy", "Solo", "Netrunner", "Tech", "Medtech",
             "Media", "Lawman", "Exec", "Nomad", "Fixer"]
    for i, r in enumerate(roles, 1):
        print(f"  {i}. {r}")
    while True:
        s = input("Введи номер (1-10): ").strip()
        if s.isdigit() and 1 <= int(s) <= 10:
            return roles[int(s) - 1]
        print("Неверный номер")


def distribute_stats():
    print("\n=== РАСПРЕДЕЛЕНИЕ СТАТОВ (62 очка, каждая 2..8) ===")
    print("Введи значение для каждой характеристики (2..8):")
    stats_list = ["INT", "REF", "DEX", "TECH", "COOL", "WILL", "LUCK", "MOVE", "BODY", "EMP"]
    stats = {}
    while True:
        total = sum(stats.values())
        print(f"\nОсталось раздать: {62 - total}")
        for s in stats_list:
            v = stats.get(s)
            while v is None:
                raw = input(f"  {s} (2..8): ").strip()
                if raw.isdigit() and 2 <= int(raw) <= 8:
                    v = int(raw)
                else:
                    print("    Введи число от 2 до 8")
            stats[s] = v
        total = sum(stats.values())
        if total == 62:
            break
        elif total < 62:
            print(f"\nСумма {total}, нужно 62. У тебя осталось {62 - total}. Начнём заново.")
        else:
            print(f"\nСумма {total}, превышение на {total - 62}. Начнём заново.")
        stats = {}
    return stats


def choose_lifepath():
    print("\n=== ПРЕДЫСТОРИЯ ===")
    while True:
        s = input("Создать самому (1) или кинуть 2d6 (2)? ").strip()
        if s in ("1", "2"):
            break
    mode = "manual" if s == "1" else "roll"

    tables = {
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
                                   "Space station / orbital", "Secure corporate arcology", "Military base"],
        "family_crisis": ["Family destroyed by war", "Family imprisoned", "Family bankrupt",
                           "Family killed by gang", "Family member killed by corporation",
                           "Family split apart", "Family member went missing",
                           "Family member betrayed you", "Family member became cyberpsycho",
                           "Family exiled you", "No crisis — stable childhood"],
    }

    lifepath = {}
    for key, options in tables.items():
        if mode == "roll":
            # 2d6 -> индекс (2..12 -> 0..10)
            d1, d2 = __import__("random").randint(1, 6), __import__("random").randint(1, 6)
            idx = d1 + d2 - 2
            choice = options[idx]
            print(f"\n  {key}: брошено {d1}+{d2}={d1+d2} → {choice}")
            lifepath[key] = choice
        else:
            print(f"\n  {key}:")
            for i, o in enumerate(options, 1):
                print(f"    {i}. {o}")
            while True:
                s = input("  Выбор (1-11): ").strip()
                if s.isdigit() and 1 <= int(s) <= len(options):
                    lifepath[key] = options[int(s) - 1]
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
    print(f"\nДополнительные навыки (10 очков, максимум 6 на навык):")
    print("Введи имя навыка и ранк (например: stealth 2). Пустая строка — завершить.")
    print("Доступные навыки: athletics, melee, evasion, stealth, handgun, shoulder_arms,")
    print("  perception, deduction, interface, programming, electronics, basic_tech,")
    print("  persuasion, conversation, first_aid, paramedic, trading, ...")
    print(f"\n  Осталось очков: 10")
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
        # Проверяем, что навык не карьерный
        if sk in career_skills:
            print(f"    Навык {sk} уже карьерный (ранк {skills[sk]})")
            continue
        # Для pickup: максимальный ранк 6 (не суммируется с карьерным)
        current = skills.get(sk, 0)
        new_val = current + rank
        if new_val > 6:
            print(f"    Превышен максимум (было {current}, +{rank} = {new_val})")
            continue
        skills[sk] = new_val
        pool -= rank
    return skills


def interactive_chargen():
    """Полный wizard создания персонажа по правилам книги."""
    print("\n" + "=" * 70)
    print("   СОЗДАНИЕ ПЕРСОНАЖА (по правилам Cyberpunk RED)")
    print("=" * 70)

    # Роль
    role = choose_role()
    role_info = requests.post(f"{API}/chargen/roleinfo", json={"role": role}, timeout=10).json() \
        if False else None  # пока не нужен отдельный эндпоинт
    career_skills = {
        "Rockerboy": ["performance", "persuasion", "human_perception", "acting"],
        "Solo": ["handgun", "melee", "evasion", "athletics"],
        "Netrunner": ["interface", "programming", "electronics", "perception"],
        "Tech": ["basic_tech", "electronics", "cybertech", "weaponstech"],
        "Medtech": ["paramedic", "first_aid", "pharmaceuticals", "human_perception"],
        "Media": ["deduction", "library_search", "persuasion", "acting"],
        "Lawman": ["handgun", "perception", "deduction", "criminology"],
        "Exec": ["persuasion", "conversation", "deduction", "trading"],
        "Nomad": ["drive", "land_vehicle_tech", "athletics", "perception"],
        "Fixer": ["streetwise", "persuasion", "conversation", "trading"],
    }[role]
    print(f"\nРоль: {role} | Карьерные навыки: {', '.join(career_skills)}")

    # Статы
    stats = distribute_stats()

    # Lifepath
    lifepath = choose_lifepath()

    # Навыки
    skills = distribute_skills(career_skills)

    # Имя и стиль
    name = input("\nИмя/хэндл: ").strip() or "Чоум"
    style = input("Визуальная деталь (или Enter): ").strip()

    # Собираем персонажа
    ch = {
        "name": name, "role": role,
        "stats": stats, "skills": skills,
        "hp": stats["BODY"] * 2, "max_hp": stats["BODY"] * 2,
        "wound": "unharmed", "dsp": 0, "dead": False,
        "humanity": stats["EMP"] * 10,
        "lifepath": lifepath,
    }
    if style:
        ch["style"] = style

    # Валидация на сервере
    resp = requests.post(f"{API}/chargen/validate", json=ch, timeout=10)
    v = resp.json()
    if not v["valid"]:
        print(f"\n[ошибка] Проблемы валидации: {v['problems']}")
        print("Вернись и поправь, либо используй random.")
        return None
    return ch


def make_players(mode="interactive"):
    """Создаёт двух игроков. mode='interactive' — wizard, 'random' — авто."""
    players = []
    if mode == "random":
        for i in range(2):
            players.append(requests.post(f"{API}/chargen",
                                         json={"mode": "random"}, timeout=30).json())
    else:
        for i in range(2):
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
    print(f"HEAT {st['heat']} | clocks {st['clocks']} | flags {st['flags']}")
    for p in st["players"]:
        print(f"  {p['name']} [{p['role']}] HP {p['hp']}/{p['max_hp']} {p.get('wound', '')}")
    for n in st.get("npcs", []):
        print(f"  NPC {n['name']}: HP {n['hp']}/{n['max_hp']} {n.get('wound', '')}")
    print(f"Ходит: {st['order'][st['turn']]}")


def show_result(r, sid):
    m = r.get("mechanics", {})
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