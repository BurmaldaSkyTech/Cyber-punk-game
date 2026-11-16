

===== backend/main.py =====

--- CONTRACT_BEATS ---
CONTRACT_BEATS = [
    "ЦЕЛЬ: крио-капсула с нейроимплантом 'Лазарь' в дата-узле Biotechnica, промзона, sector 7.",
    "ОХРАНА: 4 guard в kevlar + сержант в heavy armorjack; патрули ходят по расписанию, смены каждые 2 часа.",
    "СЛАБОЕ МЕСТО: служебный вход с кодовым замком и слепая зона камер у северного забора.",
    "УСЛОВИЕ: имплант нужен ЦЕЛЫМ; капсулу не вскрывать до передачи Кесслеру лично в руки.",
    "СРОК: до рассвета — после смены охраны в 06:00 доступ к узлу закроется.",
]

--- ACT2_SCENE ---
ACT2_SCENE = ("Дата-узел Biotechnica, промзона sector 7, ночь. Серое здание без вывесок, "
              "камеры на углах, патрули охраны по периметру. У служебного входа — кодовый "
              "замок; северный забор уходит в слепую зону камер. Изнутри гудят серверные.")

--- ACT3_SCENE ---
ACT3_SCENE = ("Внутренний периметр дата-узла Biotechnica. Коридоры с серым линолеумом, "
              "гул серверных за стенами, камеры под потолком. Служебные двери с кодовыми "
              "замками, патрули охраны проходят каждые несколько минут. Где-то в глубине — "
              "стойка регистрации и лифт на нижние уровни.")

--- NARR_FLAVOR_SYS ---
NARR_FLAVOR_SYS = """Ты — соавтор наррации Cyberpunk RED. Верни ТОЛЬКО JSON с художественными описаниями БЕЗ исходов.
Запрещено в любых полях: слова попал/попадает/промах/урон/поглот/брон/ранен/убит/умер/SP/кевлар/луч/лазер/плазма, любые цифры и DV.
Поля:
"action": 1-2 предложения описания действия игрока (жест, движение, звук, атмосфера), без исхода.
"hit": 1 предложение ощущения/картинки момента контакта или промаха, без исхода и цифр.
"shots": массив ровно по числу выстрелов NPC; каждый элемент — 1 предложение картинки выстрела (трассер, гильза, вспышка, укрытие), без исхода.
"principal": 1 предложение поведения не-бойца (фиксер/гражданский) в момент опасности, без исхода.
Стиль: нуар, неон, дым, конкретные детали. Имена не упоминай — их подставит сервер.
"""

--- NARR_HARD_RULES ---
NARR_HARD_RULES = """=== ЖЁСТКИЕ ПРАВИЛА (нарушать запрещено) ===
1. Оружие здесь — ОБЫЧНОЕ огнестрельное и холодное: пули, вспышка из ствола, дым, гильзы, лязг затвора.
   ЗАПРЕЩЕНЫ слова и образы: "пульсарный луч", "лазер", "плазма", "энергетический луч", "луч из пистолета",
   "обгоревшая кожа" от ножа или пули. Нож режет и колет, пуля пробивает или рикошетит.
2. Описывай ТОЛЬКО выстрелы и удары, перечисленные в ПОСЛЕДСТВИЯХ. Нет строки выстрела телохранителя —
   не придумывай его. Строка "ПРОМАХ" — опиши промах (пуля в стену, мимо головы), а не попадание.
3. Все выстрелы NPC направлены в игрока, указанного как target_player. Не меняй цель и не добавляй новых стрелков.
4. Крит-травма принадлежит ЦЕЛИ атаки (имя в строке крита), а не стрелку.
5. Не-боец (фиксер, гражданский), по которому ударили, ныряет за укрытие и зовёт охрану, но НЕ стреляет,
   если в последствиях указано "сам НЕ стреляет".
6. Броня поглотила урон (net=0): опиши удар, рикошет, искры от брони; цель НЕ ранена. Не пиши "увернулся".
"""

--- JUDGE_SYS ---
JUDGE_SYS = """Ты — механический интерпретатор правил Cyberpunk RED. Никакой прозы, только JSON:
{"action_type": "skill|attack_ranged|attack_melee|hack|social|heal|free",
 "skill": "ключ навыка строго из списка персонажа или null",
 "dv_key": "simple|everyday|difficult|professional|heroic|incredible|legendary или null",
 "weapon": "ключ оружия или null", "target": "id NPC или null",
 "second": null или такой же объект для ВТОРОЙ части составного действия,
 "query": "короткий запрос для поиска правил или null"}
 Для атак добавляй поле "location": "head" | "torso" | "limb" | "auto" — куда целится игрок.
"стреляет в голову" / "бьёт в шею" -> "head"; "в корпус/грудь" -> "torso"; "по руке/ноге" -> "limb"; иначе "auto".

=== ПРИОРИТЕТЫ (проверяй СНАЧАЛА, сверху вниз) ===

1. АТАКА: выстрел, удар, бросок гранаты → attack_ranged / attack_melee.
   ⚠️ ВАЖНО: фразы "давай нападай", "ну попробуй", "подойди ближе", "попробуй достать" БЕЗ явного упоминания оружия/удара — это НЕ атака. Это провокация (social) или ожидание (free).
   Атака ТОЛЬКО если есть: "стреляю", "бью", "кидаю", "атакую", "выстрел", "удар", "бросаю гранату", "замахиваюсь".
   ❌ НЕ атака: "ну давай, нападай", "попробуй", "давай-давай", "подойди"
   ✅ Атака: "стреляю в Кесслера", "бью его кулаком", "кидаю в него стул", "замахиваюсь ножом"

2. ВЗЛОМ: сеть, электроника, замки, камеры → hack или skill.

3. СОЦИАЛКА (если есть ЛЮБОЕ из): обращение к NPC по имени, просьба ("дай", "одолжи", "можно", "разреши", "покажи", "расскажи"), вопрос NPC ("расскажи", "объясни", "а что если"), убеждение, торг, ложь, лесть, провокация ("ну давай", "попробуй", "нападай", "подойди") → social.
   ВАЖНО: если игрок говорит "дай X и мы пойдём" / "одолжи Y на дело" / "покажи контракт" — это ВСЁ ЕЩЁ social, потому что главное — просьба/приказ, а "пойдём" лишь аргумент.
   Провокации типа "ну давай нападай", "ну попробуй достать" — это social (навык intimidation или persuasion).

4. НАВЫК: скрытность, акробатика, вождение, поиск, медицина и т.п. без обращения к NPC → skill.
   ⚠️ ТРИВИАЛЬНЫЕ ДЕЙСТВИЯ: чтение текста, осмотр предмета перед собой, взгляд на объект — это simple (DV9) или free, НЕ everyday.
   ❌ НЕ everyday: "читает контракт", "осматривает планшет", "смотрит на карту"
   ✅ everyday: "ищет скрытую информацию", "декодирует шифр", "анализирует данные"

5. FREE (без броска): ТОЛЬКО если фраза — чистое описание состояния или команда без обращения к NPC.
   Примеры free: "Сидит на стуле", "Стоит у стены", "Пропускаю ход", "Жду", "Отправляемся", "Встаю и иду к выходу", "ну давай нападай" (ожидание атаки NPC).
   НЕ free: "Кес, дай винтовку" (social!), "Покажи контракт" (social!), "Скажи мне, работаем тихо?" (social).
   
=== ПРИМЕРЫ (для обучения, не копируй их фразы) ===

"стреляю в охранника из тяжёлого пистолета" -> {"action_type":"attack_ranged","skill":"handgun","dv_key":"difficult","weapon":"heavy_pistol","target":"guard1","second":null,"query":"ranged attack DV"}
"спрашиваю Кесслера про условия контракта" -> {"action_type":"social","skill":"conversation","dv_key":"everyday","weapon":null,"target":"kessler","second":null,"query":"social opposed check"}
"дай нам автоматическую винтовку и мы пойдём на дело" -> {"action_type":"social","skill":"persuasion","dv_key":"everyday","weapon":null,"target":"kessler","second":null,"query":"social opposed check"}
"Кес, одолжи ствол, отработаем чисто" -> {"action_type":"social","skill":"persuasion","dv_key":"everyday","weapon":null,"target":"kessler","second":null,"query":"social opposed check"}
"Покажи данные по контракту" -> {"action_type":"social","skill":"conversation","dv_key":"everyday","weapon":null,"target":"kessler","second":null,"query":"social opposed check"}
"Расскажи про охрану" -> {"action_type":"social","skill":"conversation","dv_key":"everyday","weapon":null,"target":"kessler","second":null,"query":"social opposed check"}
"торгуюсь с Кесслером о цене" -> {"action_type":"social","skill":"trading","dv_key":"everyday","weapon":null,"target":"kessler","second":null,"query":"social opposed check"}
"Сидит на стуле" -> {"action_type":"free","skill":null,"dv_key":null,"weapon":null,"target":null,"second":null,"query":null}
"Стоит у стены" -> {"action_type":"free","skill":null,"dv_key":null,"weapon":null,"target":null,"second":null,"query":null}
"Пропускаю ход" -> {"action_type":"free","skill":null,"dv_key":null,"weapon":null,"target":null,"second":null,"query":null}
"незаметно пробираюсь мимо охраны" -> {"action_type":"skill","skill":"stealth","dv_key":"difficult","weapon":null,"target":null,"second":null,"query":"stealth check DV"}
"взламываю электронный замок двери" -> {"action_type":"skill","skill":"electronics_security_tech","dv_key":"professional","weapon":null,"target":null,"second":null,"query":"security tech check"}
"Отправляемся." (одиночная команда, без NPC) -> {"action_type":"free","skill":null,"dv_key":null,"weapon":null,"target":null,"second":null,"query":null}
"Встаю и иду к выходу." (физическое действие без просьб) -> {"action_type":"free","skill":null,"dv_key":null,"weapon":null,"target":null,"second":null,"query":null}
"делаю подсечку" -> {"action_type":"attack_melee","skill":"martial_arts","dv_key":"difficult","weapon":null,"move":"sweep","target":"guard1","second":null,"query":"martial arts sweep"}
"бросаю противника через бедро" -> {"action_type":"attack_melee","skill":"martial_arts","dv_key":"professional","weapon":null,"move":"throw","target":"guard1","second":null,"query":"martial arts throw"}
"газует и уходит от погони" -> {"action_type":"drive","skill":"drive_land_vehicle","dv_key":"difficult","weapon":null,"target":null,"second":null,"query":"drive chase maneuver"}
"таранит машину охранника" -> {"action_type":"ram","skill":"drive_land_vehicle","dv_key":"professional","weapon":null,"target":"guard1","second":null,"query":"ram vehicle damage"}
"ну давай, нападай" -> {"action_type":"social","skill":"intimidation","dv_key":"everyday","weapon":null,"target":"kessler","second":null,"query":"intimidation check"}
"читает контракт на столе" -> {"action_type":"skill","skill":"perception","dv_key":"simple","weapon":null,"target":null,"second":null,"query":"reading DV"}
"осматривает планшет" -> {"action_type":"skill","skill":"perception","dv_key":"simple","weapon":null,"target":null,"second":null,"query":"perception check"}
"ну попробуй достать" -> {"action_type":"free","skill":null,"dv_key":null,"weapon":null,"target":null,"second":null,"query":null}

dv_key: тривиально -> everyday; настороже -> difficult; защита -> professional; на грани -> heroic.
skill строго из списка персонажа.
Верни ТОЛЬКО JSON."""

--- detect_departure_intent ---
def detect_departure_intent(text):
    """Определяет намерение уйти из бара.
    
    Возвращает (wants_to_leave, confirm_yes, confirm_no).
    Отыгрыш в *звёздочках* игнорируется: жесты не переключают акт.
    """
    clean = re.sub(r"\*[^*]*\*", " ", text or "").lower()
    words = re.findall(r"[a-zа-яё0-9]+", clean)
    neg = any(n in clean for n in NEG_DEPARTURE)
    leave = (not neg) and any(t in words for t in ACT2_TRIGGERS_WORDS)
    yes = any(w in words for w in CONFIRM_YES)
    no = any(w in words for w in CONFIRM_NO)
    return leave, yes, no

--- sanitize_flavor ---
def sanitize_flavor(flavor, n_shots):
    flavor = flavor if isinstance(flavor, dict) else {}
    raw_shots = flavor.get("shots") or []
    return {
        "action": _clean_flavor(flavor.get("action"), "движение резкое, без предупреждения"),
        "hit": _clean_flavor(flavor.get("hit"), ""),
        "shots": [_clean_flavor(raw_shots[i] if i < len(raw_shots) else "",
                                "трассер режет дым над стойкой") for i in range(n_shots)],
        "principal": _clean_flavor(flavor.get("principal"), "вжимается в укрытие за столом"),
    }

--- assemble_narration ---
def assemble_narration(mech, actor_name, flavor):
    """Исходы всегда из механики; художественный текст — только из flavor-слотов."""
    lines = []
    at = mech.get("action_type")
    if mech.get("no_roll"):
        lines.append(f"{actor_name}: {flavor['action']}. Действие не требует броска.")
    elif at in ("attack_ranged", "attack_melee"):
        lines.append(f"{actor_name}: {flavor['action']}.")
        if flavor["hit"]:
            lines.append(flavor["hit"])
        lines += _attack_outcome_lines(mech)
        second = mech.get("second")
        if isinstance(second, dict) and second.get("action_type") in ("attack_ranged", "attack_melee"):
            lines += _attack_outcome_lines(second)
    else:
        lines.append(f"{actor_name}: {flavor['action']}.")
        lines.append(f"Проверка {mech.get('stat_key')}+{mech.get('skill')}: "
                     f"{mech.get('total')} против DV{mech.get('dv')} — "
                     f"{'УСПЕХ' if mech.get('success') else 'ПРОВАЛ'}.")
        if flavor["hit"]:
            lines.append(flavor["hit"])

    r = mech.get("npc_reaction")
    if r:
        shots = r.get("shots", [])
        for i, s in enumerate(shots):
            fl = flavor["shots"][i] if i < len(flavor["shots"]) else "трассер режет дым над стойкой"
            if s["success"]:
                net = s.get("net_damage", 0)
                if net > 0:
                    out = (f"пуля попадает в {r.get('target_player')}: урон {s.get('damage', 0)} - "
                           f"SP{s.get('armor_sp', 0)} = {net}, HP игрока {s.get('player_hp', '?')}.")
                else:
                    out = (f"пуля попадает в {r.get('target_player')}, но броня SP{s.get('armor_sp', 0)} "
                           f"поглощает весь урон {s.get('damage', 0)}: раны нет.")
            else:
                out = f"выстрел в {r.get('target_player')} проходит мимо."
            lines.append(f"{s['npc']}: {fl}. {out}")
        p = r.get("principal")
        if p:
            lines.append(f"{p['npc']}: {flavor['principal']}. {p['text']}.")
    return "\n".join(lines)

--- consequences ---
def consequences(mech):
    cons = []
    items = [mech] + ([mech["second"]] if isinstance(mech.get("second"), dict) else [])
    for m in items:
        if m.get("damage") is not None:
            net = m.get("net_damage", 0)
            if net == 0 and not m.get("critical_injury"):
                cons.append(f"- УСПЕШНОЕ попадание по {m.get('target')}: броня поглотила ВЕСЬ урон "
                            f"(урон {m.get('damage')} - SP{m.get('armor_sp')} = 0), "
                            f"цель НЕ ранена, но удар пришёлся")
            elif net > 0:
                cons.append(f"- УСПЕШНОЕ попадание по {m.get('target')}: сквозь броню {net}"
                            + (f", КРИТ-ТРАВМА У {m.get('target')}: {m.get('critical_injury')}"
                               if m.get("critical_injury") else "")
                            + f", у цели HP {m.get('target_hp')} ({m.get('target_wound')})")
            else:
                cons.append(f"- попадание по {m.get('target')}: урон {net}")

    r = mech.get("npc_reaction")
    if r:
        cons.append(f"- ВСЕ выстрелы NPC ниже направлены ТОЛЬКО в игрока {r.get('target_player')}:")
        for s in r.get("shots", []):
            if s["success"]:
                cons.append(f"  * {s['npc']} стреляет в {r.get('target_player')}: ПОПАДАНИЕ, "
                            f"урон {s.get('damage', 0)} - SP{s.get('armor_sp', 0)} = {s.get('net_damage', 0)}"
                            + (f", КРИТ У ИГРОКА: {s.get('critical_injury')}" if s.get("critical_injury") else ""))
            else:
                cons.append(f"  * {s['npc']} стреляет в {r.get('target_player')}: ПРОМАХ "
                            f"({s['total']} vs DV{s['dv']})")
        p = r.get("principal")
        if p:
            cons.append(f"- {p['npc']} (не боец): {p['text']}")
    return "\n".join(cons) or "- урон не наносился"

--- suggest_followups ---
def suggest_followups(st, mech):
    act = st.get("act", "fixer")
    base = {
        "fixer": ["Расспросить о контракте (persuasion)",
                  "Поторговаться об авансе (trading)",
                  "Осмотреть телохранителей (perception)"],
        "recon": ["Осмотреть периметр (perception)",
                  "Вычислить маршрут патрулей (deduction)",
                  "Взломать камеру (hack)"],
        "infiltration": ["Прокрасться мимо охраны (stealth)",
                         "Взломать замок (hack)",
                         "Отвлечь охранника (persuasion)"],
    }.get(act, [])
    if not mech.get("no_roll") and not mech.get("success"):
        base = base + ["Повторить попытку другим путём"]
    return base[:4]

--- _act_core ---
def _act_core(sid: str, req: ActionIn):
    st = get_state(sid)
    if not st:
        raise HTTPException(404)

    actor = next((p for p in st["players"] if p["name"] == req.player), None)
    if not actor:
        raise HTTPException(404, "no such player")

    expected = st["order"][st["turn"]]
    if req.player != expected:
        raise HTTPException(409, f"Сейчас ходит {expected}, а не {req.player}")

    scene = st["scenario"].get("scene", "")
    npc_lines = "; ".join(f"{n['id']}={n['name']}" for n in st["npcs"])
    threat = next((n["name"] for n in st["npcs"] if n["id"] == st.get("threat")), "нет")

    judge = chat_json([
        {"role": "system", "content": JUDGE_SYS},
        {"role": "user", "content":
            f"Сцена: {scene}\nNPC: {npc_lines}\nТЕКУЩАЯ УГРОЗА: {threat}\n"
            f"Навыки персонажа: {actor['skills']}\n"
            f"Оружие доступно: {list(engine.WEAPONS.keys())}\nДействие: {req.text}"}
    ], model=JUDGE_MODEL, temperature=0.1)
    judge["_text"] = req.text

    assist = None
    if req.assist:
        helper = next((p for p in st["players"] if p["name"] == req.assist), None)
        if helper:
            assist = engine.resolve_assist(
                st, helper, engine.DV.get(judge.get("dv_key", "everyday"), 13),
                engine.SKILL_STAT.get(judge.get("skill", ""), "COOL"), judge.get("skill", ""))

    mech = engine.resolve_check(st, actor, judge)
    second = judge.get("second")
    if isinstance(second, dict) and second.get("action_type"):
        second["_text"] = req.text
        mech["second"] = engine.resolve_check(st, actor, second)
    if assist and assist.get("bonus"):
        mech["total"] += assist["bonus"]
        mech["success"] = mech["total"] >= mech["dv"]
        mech["assist"] = assist

    if not mech.get("no_roll"):
        reaction = engine.resolve_npc_reaction(st, actor, mech)
        if reaction:
            mech["npc_reaction"] = reaction

    for m in [mech] + ([mech["second"]] if isinstance(mech.get("second"), dict) else []):
        if m.get("target_id"):
            st["threat"] = m["target_id"]

    info_kw = ("контракт", "детал", "цель", "информац", "чертеж", "план", "узна",
               "расскаж", "что нужно", "задан", "вопрос")
    is_info = (mech.get("action_type") in ("social", "hack", "skill")
               and not mech.get("no_roll")
               and any(k in req.text.lower() for k in info_kw))
    if is_info and mech.get("success"):
        remaining = [b for b in CONTRACT_BEATS if b not in st["revealed_beats"]]
        if remaining:
            st["revealed_beats"].append(remaining[0])

    # === АКТЫ И ПЕРЕХОДЫ ===
    act_type = st.get("act", "fixer")
    do_transition = False
    departure_question = False
    act_notice = ""

    if act_type == "fixer":
        st["fixer_round"] = st.get("fixer_round", 0) + 1
        if mech.get("action_type") == "social" and not mech.get("no_roll") and not mech.get("success"):
            st["patience"] = st.get("patience", 4) - 1

        leave, yes, no = detect_departure_intent(req.text)
        recent_logs = st["log"][-4:]
        fail_count = sum(1 for lg in recent_logs if lg.get("mech", {}).get("success") is False)
        kessler_tired = fail_count >= 3 or st.get("patience", 4) <= 0

        if st.get("pending_departure"):
            if no:
                st["pending_departure"] = False
            elif yes or leave:
                st["pending_departure"] = False
                do_transition = True
        elif kessler_tired:
            do_transition = True
        elif leave:
            st["pending_departure"] = True
            departure_question = True

        if do_transition:
            scenario.advance_act(st)
            st["act"] = "recon"
            st["recon_slots"] = 3
            st["assets"] = []
            st["scenario"]["scene"] = ACT2_SCENE
            transition_narr = (
                ("Кесслер нетерпеливо машет рукой: 'Хватит болтать, время идёт. Идите и сделайте свою работу.' "
                 "Он забирает планшет и уходит, не оглядываясь."
                 if kessler_tired else
                 "Вы поднимаетесь из-за стола. Кесслер кивает на прощание: 'Удачи. Не подведите.' "
                 "Он сворачивает планшет и уходит вглубь бара.")
                + "\n\n[ПЕРЕХОД К АКТУ 2: РЕКОГНОСЦИРОВКА]\n\n" + ACT2_SCENE)
            st["log"].append({"player": "GM", "text": "[переход]", "mech": {}, "narration": transition_narr})
            turn_no = len(st["log"]) - 1
            turn_id = db.log_turn(sid, turn_no, "GM", "[переход]", {}, {}, transition_narr)
            return {
                "mechanics": {"action_type": "free", "no_roll": True},
                "narration": transition_narr,
                "questions": ["Что вы делаете для рекогносцировки?"],
                "choices": suggest_followups(st, {"no_roll": True}),
                "turn_no": turn_no, "turn_id": turn_id,
                "next_player": st["order"][0],
                "state": public_state(st),
            }

    elif act_type == "recon":
        if mech.get("action_type") in ("skill", "hack", "social") and not mech.get("no_roll"):
            st["recon_slots"] = st.get("recon_slots", 0) - 1
            if mech.get("success"):
                st.setdefault("assets", []).append(
                    {"skill": judge.get("skill"), "note": req.text[:60]})
        if st.get("recon_slots", 0) <= 0:
            scenario.advance_act(st)
            st["act"] = "infiltration"
            st["suspicion"] = 0
            st["lockdown"] = 0
            st["scenario"]["scene"] = ACT3_SCENE
            act_notice = "[ПЕРЕХОД К АКТУ 3: ПРОНИКНОВЕНИЕ]\n\n" + ACT3_SCENE

    elif act_type == "infiltration":
        if not mech.get("no_roll") and not mech.get("success"):
            st["suspicion"] = st.get("suspicion", 0) + 1
            if st["suspicion"] >= 3:
                st["suspicion"] = 0
                st["lockdown"] = st.get("lockdown", 0) + 1
                act_notice = f"[ТРЕВОГА: уровень локдауна {st['lockdown']}/6] Охрана ужесточает патрули."
                if st["lockdown"] >= 6 and "alarm" not in st.get("flags", []):
                    st.setdefault("flags", []).append("alarm")
                    act_notice += " ОБЪЕКТ ПОЛНОСТЬЮ ЗАБЛОКИРОВАН."

    # === НАРРАЦИЯ: исходы из механики, художественность из flavor-слотов ===
    actor_name = actor["name"]
    shots_n = len((mech.get("npc_reaction") or {}).get("shots", []))
    prev_short = (st["log"][-1]["narration"][:160] if st["log"] else "")
    flavor_raw = chat_json([
        {"role": "system", "content": NARR_FLAVOR_SYS},
        {"role": "user", "content":
            f"Игрок: {actor_name}\nДействие: {req.text}\nСцена: {scene[:200]}\n"
            f"Предыдущий момент: {prev_short}\n"
            f"Тип: {mech.get('action_type')}, исход: "
            f"{'без броска' if mech.get('no_roll') else ('успех' if mech.get('success') else 'провал')}\n"
            f"Выстрелов NPC: {shots_n}\nВерни JSON flavor."}
    ], model=globals().get("NARR_MODEL", JUDGE_MODEL), temperature=0.7)
    narration = assemble_narration(mech, actor_name, sanitize_flavor(flavor_raw, shots_n))

    if departure_question:
        narration += ("\n\nКесслер смотрит выжидающе: "
                      "«Уверены, что уходите? Контракт останется невыполненным.»")
    if act_notice:
        narration += "\n\n" + act_notice

    # === ЛОГ, ХОД, СПАСБРОСКИ ===
    st["log"].append({"player": actor_name, "text": req.text, "mech": mech, "narration": narration})
    turn_no = len(st["log"]) - 1
    turn_id = db.log_turn(sid, turn_no, actor_name, req.text, mech, {}, narration)

    alive = [p for p in st["players"] if not p.get("dead")]
    if alive:
        for _ in range(len(st["order"])):
            st["turn"] = (st["turn"] + 1) % len(st["order"])
            if not st["players"][st["turn"]].get("dead"):
                break

    for p in st["players"]:
        if p.get("wound") == "mortally" and not p.get("dead"):
            p["death_save"] = engine.death_save(p)

    return {
        "mechanics": mech,
        "assist": assist,
        "narration": narration,
        "questions": [],
        "choices": suggest_followups(st, mech),
        "turn_no": turn_no,
        "turn_id": turn_id,
        "next_player": st["order"][st["turn"]],
        "state": public_state(st),
    }
 
   # Контекст нетраннинга
    net_context = ""
    if mech.get("hack_result") == "entered":
        net_context = (f"\nНЕТРАННИНГ: {actor_name} вошёл в сеть '{mech.get('architecture')}'. "
                      f"Этаж {mech.get('floor')}/{mech.get('max_floors')}, DV {mech.get('dv')}.") 
                      

    # Тик активных эффектов наркотиков
    for p in st["players"]:
        expired = substances.tick_effects(p)
        if expired:
            st["flags"].append(f"effect_expired:{','.join(expired)}") 

    # Контекст транспорта и погони
    from backend import vehicles as veh_mod
    transport_lines = []
    for p in st["players"]:
        if p.get("vehicle"):
            v = veh_mod.get_vehicle(p["vehicle"])
            transport_lines.append(f"- {p['name']}: в транспорте {(v or {}).get('name', p['vehicle'])}")
    chase = st.get("chase")
    chase_line = ""
    if chase and chase.get("status") == "active":
        chase_line = (f"\nПОГОНЯ: дистанция {chase['range']} ({chase.get('range_name', '')}), "
                      f"раунд {chase['rounds']}")
    transport_ctx = ""
    if transport_lines or chase_line:
        transport_ctx = "\nТРАНСПОРТ В СЦЕНЕ:\n" + "\n".join(transport_lines) + chase_line + "\n"

    # Явный флаг: успех, но броня поглотила
    success_but_blocked = (
        mech.get("success") 
        and mech.get("net_damage", 0) == 0 
        and mech.get("damage", 0) > 0
    )

    user_msg = (
        f"ДЕЙСТВУЕТ: {actor_name}\n"
        f"ИГРОКИ В СЦЕНЕ: {players_names}\n"
        f"ИМЕНА: используй ТОЛЬКО имена из блоков ДЕЙСТВУЕТ, ИГРОКИ В СЦЕНЕ и NPC В СЦЕНЕ. "
        f"ЗАПРЕЩЕНО подставлять любые другие имена (Вектор, Никс и т.п.). "
        f"Если имя — число или нестандартное слово, пиши его БЕЗ склонения.\n"
        f"СЦЕНА: {scene}\n{act_ctx}\n"
        f"NPC В СЦЕНЕ:\n{npc_block}\n"
        + transport_ctx
        + f"Heat: {st['heat']}, флаги: {st['flags']}\n"        
        f"Heat: {st['heat']}, флаги: {st['flags']}\n"
        f"ПЕРСОНАЖ ИГРОКА: {actor_name} ({actor['role']})\n"
        f"ЗАЯВЛЕНОЕ ДЕЙСТВИЕ: {req.text}\n"
        f"СМЫСЛ ДЕЙСТВИЯ: {ACTION_LABEL.get(mech.get('action_type'), 'действие')}\n"
        f"ФАКТЫ БРОСКА: {facts}\nРЕЗУЛЬТАТ: {outcome}\n"
        f"ПОСЛЕДСТВИЯ (обязательно соблюдать):\n{cons}\n"
        + (f"ВОПРОС-ПОДТВЕРЖДЕНИЕ: игрок заявил уход из бара, но ещё НЕ подтвердил его. "
           f"В конце нарратива ОБЯЗАТЕЛЬНО задай вопрос: 'Уверены, что уходите? Контракт останется невыполненным.' "
           f"НЕ описывай сам уход и НЕ покидай бар в этом ходе.\n" if departure_question else "")        
        + (f"ВНИМАНИЕ: УСПЕХ, но броня поглотила весь урон. Цель НЕ ранена, но удар пришёлся. НЕ пиши 'уворачивается'.\n" if success_but_blocked else "")        
        + (f"РАСКРОЙ ФАКТ СЕЙЧАС (обязательно вплести в реплику NPC конкретно):\n- {just_revealed}\n" if just_revealed else "")
        + (f"УЖЕ РАСКРЫТО РАНЬШЕ (не повторяй без вопроса):\n" + "\n".join("- " + b for b in st["revealed_beats"][:-1]) + "\n" if len(st["revealed_beats"]) > 1 else "")
        + (f"ФИЗИЧЕСКИ ВЫДАНО ИГРОКУ (на руках, учитывай в сценах):\n" + "\n".join("- " + g for g in st["granted"]) + "\n" if st.get("granted") else "")
        + (f"ПРЕДЫДУЩИЕ ХОДЫ:\n{prev}\n" if prev else "")
        + f"ПРАВИЛА (справочно):\n{ctx}\nЛОР (только названия и детали):\n{fctx}"
        + net_context
        + f"ПРАВИЛА (справочно):\n{ctx}\nЛОР (только названия и детали):\n{fctx}"
    )        

    narr_sys = NARR_SYS_UNIVERSAL

    reply = chat_json([
        {"role": "system", "content": NARR_HARD_RULES + "\n" + NARR_SYS_UNIVERSAL},
        {"role": "user", "content": user_msg}
    ], model=NARR_MODEL, temperature=0.6)

    raw_n = reply.get("narration", "")
    hallucination_keywords = ["новый сент-джеймс", "клан королевских", "покровительств"]
    you_patterns = [
        " ты ", "твой ", "твоя ", "твоё ", "твои ", "тебя ", "тебе ",
        " тобой", " твой ", " твоя ", " твоё ", " твои ",
        " вашего", " вашим", " ваша", " ваше"
    ]
    has_hallucination = any(kw in raw_n.lower() for kw in hallucination_keywords)
    has_you = any(p in raw_n.lower() for p in you_patterns)
    leaked = leaked_example_names(raw_n, st)
    has_cjk = bool(CJK.search(raw_n))
    too_short = len(clean(raw_n)) < 40

    if has_you or has_hallucination or leaked or has_cjk or too_short:
        retry_sys = narr_sys + (
            "\n\n**ВТОРАЯ ПОПЫТКА. ПРЕДЫДУЩИЙ ОТВЕТ НАРУШАЛ ПРАВИЛА: "
            "обращение на «ты», выдуманные локации/фракции, чужие имена или слишком короткий текст. "
            "Пиши ТОЛЬКО в третьем лице. Используй ТОЛЬКО имена из блоков ДЕЙСТВУЕТ, "
            "ИГРОКИ В СЦЕНЕ и NPC В СЦЕНЕ. Используй ТОЛЬКО факты из контекста.**"
        )
        reply = chat_json([
            {"role": "system", "content": retry_sys},
            {"role": "user", "content": user_msg}
        ], model=NARR_MODEL, temperature=0.4)
        raw_n = reply.get("narration", "")
        leaked = leaked_example_names(raw_n, st)

    if leaked:
        for bad in leaked:
            raw_n = re.sub(rf"\b{bad}\w*", actor_name, raw_n, flags=re.IGNORECASE)
        reply["narration"] = raw_n

    sug = clamp_suggestions(reply.get("safe_state_suggestions"), st)
    st["heat"] = max(0, min(10, st["heat"] + sug["heat_delta"]))
    st["flags"] += sug["add_flags"]
    for cname, inc in sug["clock_progress"].items():
        if cname in st["clocks"]:
            st["clocks"][cname]["progress"] = min(
                st["clocks"][cname]["max"], st["clocks"][cname]["progress"] + inc)
    if sug["npc_action"]:
        st["flags"].append(sug["npc_action"])
    st["granted"] = st.get("granted", []) + [g for g in sug["grant_items"]
                                             if g not in st.get("granted", [])]

    act_type = st.get("act", "fixer")
    do_transition = False
    departure_question = False

    act_type = st.get("act", "fixer")
    do_transition = False
    departure_question = False

    if act_type == "fixer":
        leave, yes, no = detect_departure_intent(req.text)

        recent_logs = st["log"][-4:]
        fail_count = sum(1 for lg in recent_logs if lg.get("mech", {}).get("success") is False)
        patience_low = st.get("patience", 4) <= 0
        kessler_tired = fail_count >= 3 or patience_low

        if st.get("pending_departure"):
            if no:
                st["pending_departure"] = False
            elif yes or leave:
                st["pending_departure"] = False
                do_transition = True
        elif kessler_tired:
            do_transition = True
        elif leave:
            st["pending_departure"] = True
            departure_question = True

        if do_transition:
            scenario.advance_act(st)
            st["act"] = "recon"
            st["recon_slots"] = 3
            st["assets"] = []
            st["scenario"]["scene"] = ACT2_SCENE

            if kessler_tired and not st.get("pending_departure"):
                transition_narr = ("Кесслер нетерпеливо машет рукой: 'Хватит болтать, время идёт. "
                                   "Идите и сделайте свою работу.' Он забирает планшет и уходит, "
                                   "не оглядываясь.\n\n[ПЕРЕХОД К АКТУ 2: РЕКОГНОСЦИРОВКА]\n\n"
                                   + ACT2_SCENE)
            else:
                transition_narr = ("Вы поднимаетесь из-за стола. Кесслер кивает на прощание: "
                                   "'Удачи. Не подведите.' Он сворачивает планшет и уходит вглубь бара.\n\n"
                                   "[ПЕРЕХОД К АКТУ 2: РЕКОГНОСЦИРОВКА]\n\n"
                                   + ACT2_SCENE)

            st["log"].append({"player": "GM", "text": "[переход]", "mech": {}, "narration": transition_narr})
            turn_no = len(st["log"]) - 1
            turn_id = db.log_turn(sid, turn_no, "GM", "[переход]", {}, {}, transition_narr)

            return {
                "mechanics": {"action_type": "free", "no_roll": True},
                "narration": transition_narr,
                "questions": ["Что вы делаете для рекогносцировки?"],
                "choices": ["Осмотреть территорию (perception)", "Вычислить патрули (deduction)", "Найти контакт внутри (streetwise)"],
                "turn_no": turn_no,
                "turn_id": turn_id,
                "next_player": st["order"][0],
                "state": public_state(st),
            }

    narration = clean(reply.get("narration", ""))
    questions = [clean(q) for q in reply.get("questions", []) if clean(q)]
    choices = [clean(c) for c in reply.get("choices", []) if clean(c)]

    st["log"].append({"player": req.player, "text": req.text, "mech": mech,
                      "narration": narration})
    turn_no = len(st["log"]) - 1
    turn_id = db.log_turn(sid, turn_no, req.player, req.text, judge, mech, narration)
    st["turn"] = (st["turn"] + 1) % len(st["order"])

    for p in st["players"]:
        if p.get("wound") == "mortally" and not p.get("dead"):
            p["death_save"] = engine.death_save(p)

    return {"mechanics": mech, "assist": assist, "narration": narration,
            "questions": questions, "choices": choices,
            "turn_no": turn_no, "turn_id": turn_id,
            "next_player": st["order"][st["turn"]], "state": st}

--- act ---
def act(sid: str, req: ActionIn):
    st = get_state(sid)
    if not st:
        raise HTTPException(404)

    # Проверка токена ДО обработки действия
    if st.get("tokens"):
        if st["tokens"].get(req.player) != req.token:
            raise HTTPException(403, "Неверный токен игрока")

    result = _act_core(sid, req)

    if result is None:
        print(f"[ERROR] act() вернула None: sid={sid}, player={req.player}, text={req.text!r}")
        result = {
            "mechanics": {"action_type": "free", "no_roll": True},
            "narration": "(Внутренняя ошибка: ветка act() без возврата. Действие учтено как свободное.)",
            "questions": [],
            "choices": [],
            "turn_no": (len(st["log"]) - 1) if st else 0,
            "turn_id": None,
            "next_player": st["order"][st["turn"]] if st else "",
            "state": public_state(st),
        }

    # Сохраняем и рассылаем ВСЕГДА (и успех, и fallback)
    persist(st)
    broadcast_now(sid, {"type": "state", "state": public_state(st)})
    return result


===== backend/engine.py =====

--- resolve_check ---
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
    mech["location"] = (judge or {}).get("location") or "auto"    
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

--- resolve_npc_reaction ---
def resolve_npc_reaction(st, actor, mech):
    """Все враждебные NPC сцены стреляют ТОЛЬКО по атакующему игроку.

    Не-боец (фиксер и т.п.), по которому ударили, уходит в укрытие и зовёт охрану,
    но сам не стреляет. Каждый боец делает до ROF выстрелов.
    """
    if mech.get("no_roll") or not mech.get("success"):
        return None
    target_id = mech.get("target_id")
    if not target_id:
        return None

    principal = next((n for n in st["npcs"] if n["id"] == target_id), None)
    if not principal or principal.get("dead"):
        return None

    attackers = [n for n in st["npcs"] if not n.get("dead") and _is_hostile(n)]
    if _is_hostile(principal) and principal not in attackers:
        attackers.insert(0, principal)

    shots = []
    for npc in attackers:
        wkey = _npc_weapon_key(npc)
        weapon = WEAPONS.get(wkey, {"damage": "2d6", "rof": 2, "skill": "handgun"})
        rof = max(1, min(2, int(weapon.get("rof", 2) or 2)))
        for _ in range(rof):
            shots.append(_npc_attack_roll(npc, weapon, wkey, actor))

    principal_action = None
    if not _is_hostile(principal):
        principal_action = {
            "npc": principal["name"], "action": "cover",
            "text": "ныряет за укрытие и кричит охране, сам НЕ стреляет",
        }

    if not shots and not principal_action:
        return None

    first = shots[0] if shots else {
        "npc": principal["name"], "success": False, "total": 0, "dv": 13,
        "damage": 0, "armor_sp": 0, "net_damage": 0,
    }
    return {
        "npc": first["npc"],
        "success": first["success"],
        "total": first["total"],
        "dv": first["dv"],
        "damage": first.get("damage", 0),
        "armor_sp": first.get("armor_sp", 0),
        "net_damage": first.get("net_damage", 0),
        "shots": shots,
        "helpers": shots[1:],
        "principal": principal_action,
        "target_player": actor["name"],
    }

--- _npc_attack_roll ---
def _npc_attack_roll(npc, weapon, wkey, target_player):
    """Один выстрел NPC строго по указанному игроку."""
    stat = (npc.get("stats") or {}).get("REF", 4)
    skill = (npc.get("skills") or {}).get(weapon.get("skill", "handgun"), 3)
    roll, _ = roll_dice("1d10")
    total = roll + stat + skill
    dv = 13
    success = total >= dv

    res = {
        "npc": npc["name"], "npc_id": npc["id"],
        "success": success, "total": total, "dv": dv,
        "weapon": wkey, "target_player": target_player["name"],
    }
    if success:
        dmg, _faces = roll_dice(weapon.get("damage", "2d6"))
        sp = ARMOR.get(target_player.get("armor", "leathers"), {}).get("sp", 0)
        net = max(0, dmg - sp)
        res.update({"damage": dmg, "armor_sp": sp, "net_damage": net})
        if net > 0:
            dr = apply_damage(target_player, net, weapon_key=wkey)
            target_player["hp"] = dr["hp"]
            target_player["wound"] = dr["wound_state"]
            target_player["wound_penalty"] = dr["penalty"]
            res["player_hp"] = dr["hp"]
            res["player_wound"] = dr["wound_state"]
            if dr.get("critical_injury"):
                res["critical_injury"] = dr["critical_injury"]
    return res
