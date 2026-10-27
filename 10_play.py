# 10_play.py
import requests

API = "http://localhost:8000"

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

PLAYERS = [
    {"name": "Вектор", "role": "Solo",
     "stats": {"INT": 3, "REF": 7, "DEX": 4, "TECH": 3, "COOL": 5,
               "WILL": 4, "LUCK": 2, "MOVE": 5, "BODY": 6, "EMP": 3},
     "skills": {"handgun": 4, "melee": 3, "evasion": 3, "athletics": 3, "perception": 3},
     "hp": 12, "max_hp": 12, "wound": "unharmed", "dsp": 0, "dead": False,
     "armor": "light_armorjack"},
    {"name": "Никс", "role": "Netrunner",
     "stats": {"INT": 6, "REF": 4, "DEX": 3, "TECH": 5, "COOL": 4,
               "WILL": 4, "LUCK": 3, "MOVE": 4, "BODY": 4, "EMP": 4},
     "skills": {"interface": 4, "programming": 3, "stealth": 3, "persuasion": 3, "perception": 2},
     "hp": 8, "max_hp": 8, "wound": "unharmed", "dsp": 0, "dead": False,
     "armor": "leathers"}
]


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

    # === ОЦЕНКА ХОДА ===
    rate = input("Оценка (1-5) или Enter для пропуска: ").strip()
    if rate and rate.isdigit() and 1 <= int(rate) <= 5:
        rating = int(rate)
        edited = None
        if rating <= 3:
            print("Напиши свой вариант нарратива (или Enter для пропуска):")
            edited = input("> ").strip() or None
        try:
            requests.post(f"{API}/session/{sid}/turn/{turn_no}/rate",
                          json={"rating": rating, "edited": edited}, timeout=10)
            print(f"Оценка {rating} сохранена.")
        except Exception as e:
            print(f"Ошибка сохранения оценки: {e}")


def main():
    s = requests.post(f"{API}/session",
                      json={"players": PLAYERS, "scenario": SCENARIO}, timeout=60).json()
    sid = s["id"]
    print("сессия:", sid)
    print("команды: текст = действие | assist:Имя текст = Имя помогает текущему")
    print("пример: assist:Никс взламываю замок прилавка")
    print()

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
        show_result(r)


if __name__ == "__main__":
    main()