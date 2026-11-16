

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

--- LOCATION_RU ---
LOCATION_RU = {"head": "голова", "torso": "корпус", "limb": "конечность", "auto": "корпус"}

--- NARR_FLAVOR_SYS ---
NARR_FLAVOR_SYS = """Ты — соавтор наррации Cyberpunk RED. Верни ТОЛЬКО JSON с художественными описаниями БЕЗ исходов и БЕЗ новых предметов.
Запрещено в любых полях: слова попал/попадает/промах/урон/поглот/брон/ранен/убит/умер/SP/кевлар/луч/лазер/плазма, любые цифры и DV.
Запрещено вводить НОВЫЕ предметы, контейнеры, коробки, свертки, документы, чипы; NPC ничего не достаёт и не передаёт игроку.
Поля:
"action": 1-2 предложения о ТОМ, ЧТО ДЕЛАЕТ ИГРОК (его жест, движение, звук, атмосфера вокруг него). НЕ описывай действия NPC здесь. НЕ упоминай имена (ни игрока, ни NPC).
"hit": 1 предложение ощущения/картинки момента контакта или промаха, без исхода и цифр, без имён.
"shots": массив ровно по числу выстрелов NPC; каждый — 1 предложение картинки выстрела (трассер, гильза, вспышка, укрытие), без исхода и имён.
"principal": 1 предложение поведения не-бойца в момент опасности (укрытие, крик), без исхода, без имён, без передачи предметов.
Не повторяй формулировки предыдущего хода.
Стиль: нуар, неон, дым, конкретные детали.
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

--- ACCEPT_WORDS ---
ACCEPT_WORDS = ("беру", "согласен", "согласна", "принимаю", "подписываю", "по рукам", "deal")

--- ACT2_TRIGGERS_WORDS ---
ACT2_TRIGGERS_WORDS = [
    "отправляемся", "выдвигаемся", "уходим", "ухожу", "уйду", "идём", "идем",
    "едем", "пошёл", "пошла", "пошли", "погнали", "прощается", "покидает",
]

--- NEG_DEPARTURE ---
NEG_DEPARTURE = ["не ухожу", "никуда не", "остаюсь", "остаёмся", "остаемся",
                 "передумал", "передумала", "не пойду", "не идём", "не идем", "вернусь"]

--- CONFIRM_YES ---
CONFIRM_YES = ["да", "подтверждаю", "уходим", "идём", "идем", "пошли", "погнали", "ухожу"]

--- CONFIRM_NO ---
CONFIRM_NO = ["нет", "остаюсь", "остаёмся", "остаемся", "передумал", "передумала", "вернусь"]

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

--- _clean_flavor ---
def _clean_flavor(s, default, block=()):
    s = (s or "").strip()
    low = s.lower()
    if not s or any(t in low for t in _FLAVOR_FORBID):
        return default
    if any(b and b.lower() in low for b in block):
        return default
    return s

--- sanitize_flavor ---
def sanitize_flavor(flavor, n_shots, npc_names=(), actor_name="", declared=""):
    flavor = flavor if isinstance(flavor, dict) else {}
    block_obj = ("коробочк", "коробк", "сверток", "пакет", "достаёт", "достает",
                 "протягивает", "вручает", "передаёт", "передает", "кладёт", "кладет")
    names = tuple(npc_names) + ((actor_name,) if actor_name else ())
    raw_shots = flavor.get("shots") or []
    return {
        "action": _clean_flavor(flavor.get("action"), "выполняет заявленное действие",
                                block=names + block_obj),
        "hit": _clean_flavor(flavor.get("hit"), "", block=names + block_obj),
        "shots": [_clean_flavor(raw_shots[i] if i < len(raw_shots) else "",
                                "трассер режет дым над стойкой", block=names)
                  for i in range(n_shots)],
        "principal": _clean_flavor(flavor.get("principal"), "вжимается в укрытие за столом",
                                   block=block_obj),
    }

--- _attack_outcome_lines ---
def _attack_outcome_lines(m):
    lines = []
    loc = LOCATION_RU.get(m.get("location", "auto"), "корпус")
    if m.get("success"):
        lines.append(f"Атака ({loc}): попадание.")
        dmg = m.get("damage", 0)
        sp = m.get("armor_sp", 0)
        net = m.get("net_damage", 0)
        if net > 0:
            lines.append(f"Урон {dmg}, броня SP{sp} срезает {dmg - net}: сквозь проходит {net}. "
                         f"{m.get('target')} ранен — HP {m.get('target_hp')} ({m.get('target_wound')}).")
        else:
            lines.append(f"Урон {dmg} полностью поглощён бронёй SP{sp}: "
                         f"{m.get('target')} не ранен, но удар пришёлся.")
        if m.get("critical_injury"):
            lines.append(f"Критическая травма у {m.get('target')}: {m['critical_injury']}.")
    else:
        lines.append(f"Атака ({loc}): промах — цель уходит с линии огня.")
    return lines

--- assemble_narration ---
def assemble_narration(mech, actor_name, flavor, extra=None):
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

    for x in (extra or []):
        lines.append(x)

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

--- handover_contract ---
def handover_contract(st):
    """Фиксер выполняет свою цель: передаёт контракт и аванс. Идемпотентно."""
    if st.get("contract_given"):
        return []
    st["contract_given"] = True
    remaining = [b for b in CONTRACT_BEATS if b not in st["revealed_beats"]]
    st["revealed_beats"] = list(CONTRACT_BEATS)
    advance = (st.get("contract") or {}).get("advance") or 500
    for p in st["players"]:
        p["eb"] = p.get("eb", 0) + advance
    st.setdefault("granted", []).append("дата-планшет с контрактом")
    lines = ["Кесслер двигает по столу дата-планшет: «Контракт ваш. Аванс на счетах, детали внутри.»"]
    lines += [f"— {b}" for b in remaining]
    lines.append(f"Аванс {advance} eb каждому игроку. Планшет контракта у партии.")
    return lines

--- apply_world_ticks ---
def apply_world_ticks(st, mech):
    """Детерминированные тики мира: heat и длительности эффектов."""
    notes = []
    at = mech.get("action_type")
    if at in ("attack_ranged", "attack_melee", "ram"):
        st["heat"] = min(10, st.get("heat", 0) + 1)
    elif at in ("hack", "skill") and not mech.get("no_roll") and not mech.get("success"):
        st["heat"] = min(10, st.get("heat", 0) + 1)
    for p in st["players"]:
        expired = substances.tick_effects(p)
        if expired:
            notes.append(f"Эффекты завершились у {p['name']}: {', '.join(expired)}")
            st.setdefault("flags", []).append(f"effect_expired:{','.join(expired)}")
    return notes

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
    if st.get("threat") and not st.get("initiative_rolled"):
        order = engine.roll_initiative(st["players"] + st["npcs"])
        players_order = [n for n in order if n in st["order"]]
        if players_order:
            st["order"] = players_order
            st["turn"] = 0
        st["initiative_rolled"] = True
        st["initiative"] = order
    info_kw = ("контракт", "детал", "цель", "информац", "чертеж", "план", "узна",
               "расскаж", "что нужно", "задан", "вопрос", "сколько плат")
    is_info = (mech.get("action_type") in ("social", "hack", "skill")
               and not mech.get("no_roll")
               and any(k in req.text.lower() for k in info_kw))
    just_revealed = None
    if is_info and mech.get("success"):
        remaining = [b for b in CONTRACT_BEATS if b not in st["revealed_beats"]]
        if remaining:
            just_revealed = remaining[0]
            st["revealed_beats"].append(just_revealed)

    extra = []
    if just_revealed:
        extra.append(f"Кесслер раскрывает деталь контракта: {just_revealed}")

    clean_text = re.sub(r"\*[^*]*\*", " ", req.text).lower()
    if st.get("act", "fixer") == "fixer" and any(w in clean_text for w in ACCEPT_WORDS):
        extra += handover_contract(st)

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
            handover_lines = handover_contract(st)
            scenario.advance_act(st)
            st["act"] = "recon"
            st["recon_slots"] = 3
            st["assets"] = []
            st["scenario"]["scene"] = ACT2_SCENE
            transition_narr = (
                ("Кесслер нетерпеливо машет рукой: 'Хватит болтать, время идёт. Идите и сделайте свою работу.' "
                 if kessler_tired else
                 "Вы поднимаетесь из-за стола. Кесслер кивает на прощание: 'Удачи. Не подведите.' ")
                + ("\n" + "\n".join(handover_lines) if handover_lines else "")
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
                extra.append(f"Разведданные закреплены: {req.text[:60]}")
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

    extra += apply_world_ticks(st, mech)

    if mech.get("hack_result") == "entered":
        extra.append(f"НЕТРАННИНГ: {actor['name']} входит в сеть '{mech.get('architecture')}', "
                     f"этаж {mech.get('floor')}/{mech.get('max_floors')}, DV {mech.get('dv')}.")
    elif mech.get("hack_result") == "no_interface":
        extra.append(f"{actor['name']} тянется к порту, но Interface Plugs нет: вход в сеть невозможен.")
    elif mech.get("hack_result") in ("failed", "failed_check"):
        extra.append(f"Вход в сеть не удался: {mech.get('reason', 'проверка провалена')}.")

    from backend import vehicles as veh_mod
    tl = [f"{p['name']} в транспорте {(veh_mod.get_vehicle(p['vehicle']) or {}).get('name', p['vehicle'])}"
          for p in st["players"] if p.get("vehicle")]
    ch = st.get("chase")
    if ch and ch.get("status") == "active":
        tl.append(f"ПОГОНЯ: дистанция {ch['range']} ({ch.get('range_name', '')}), раунд {ch['rounds']}")
    if tl:
        extra.append("ТРАНСПОРТ: " + "; ".join(tl))

    actor_name = actor["name"]
    shots_n = len((mech.get("npc_reaction") or {}).get("shots", []))
    prev_short = (st["log"][-1]["text"][:120] if st["log"] else "")
    flavor_raw = chat_json([
        {"role": "system", "content": NARR_FLAVOR_SYS},
        {"role": "user", "content":
            f"Игрок: {actor_name}\nДействие: {req.text}\nСцена: {scene[:200]}\n"
            f"Предыдущий момент: {prev_short}\n"
            f"Тип: {mech.get('action_type')}, исход: "
            f"{'без броска' if mech.get('no_roll') else ('успех' if mech.get('success') else 'провал')}\n"
            f"Выстрелов NPC: {shots_n}\n"
            f"Запрещено вводить новые предметы и контейнеры; NPC ничего не передаёт.\n"
            f"Верни JSON flavor."}
    ], model=globals().get("NARR_MODEL", JUDGE_MODEL), temperature=0.7)
    narration = assemble_narration(mech, actor_name, sanitize_flavor(
        flavor_raw, shots_n,
        npc_names=[n["name"] for n in st["npcs"]],
        actor_name=actor_name, declared=req.text), extra=extra)

    if departure_question:
        narration += ("\n\nКесслер смотрит выжидающе: "
                      "«Уверены, что уходите? Контракт останется невыполненным.»")
    if act_notice:
        narration += "\n\n" + act_notice

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

--- chargen_endpoint ---
def chargen_endpoint(req: ChargenIn):
    from backend import creation
    try:
        return creation.random_character(req.role)
    except Exception as e:
        raise HTTPException(400, f"chargen: {e}")

--- creation_options ---
def creation_options(role: str = None):
    from backend import creation
    return creation.options(role)

--- creation_build ---
def creation_build(spec: dict):
    from backend import creation
    try:
        return creation.build(spec)
    except ValueError as e:
        raise HTTPException(400, str(e))

--- lobby_create ---
def lobby_create(req: CreateLobby):
    sid = uuid.uuid4().hex[:8]
    code = "".join(_random.choices(string.ascii_uppercase + string.digits, k=6))
    token = uuid.uuid4().hex

    ch = dict(req.character)
    ch["name"] = req.player_name

    st = {
        "id": sid, "code": code,
        "scenario": DEFAULT_SCENARIO,
        "heat": 1, "clocks": {}, "flags": [], "log": [],
        "turn": 0, "threat": None,
        "order": [ch["name"]],
        "players": [ch],
        "npcs": [dict(n) for n in DEFAULT_SCENARIO["npcs"]],
        "revealed_beats": [], "granted": [],
        "tokens": {ch["name"]: token},
        "status": "lobby",
        **scenario.init_scenario(),
    }
    persist(st)
    return {"sid": sid, "code": code, "token": token, "state": public_state(st)}

--- lobby_join ---
def lobby_join(req: JoinLobby):
    st = find_by_code(req.code)
    if not st:
        raise HTTPException(404, "Комната не найдена")
    if st.get("status") != "lobby":
        raise HTTPException(400, "Игра уже началась")
    if req.player_name in st["order"]:
        raise HTTPException(400, "Имя занято")
    if len(st["order"]) >= 4:
        raise HTTPException(400, "Комната заполнена (максимум 4)")

    token = uuid.uuid4().hex
    ch = dict(req.character)
    ch["name"] = req.player_name
    st["players"].append(ch)
    st["order"].append(ch["name"])
    st["tokens"][ch["name"]] = token
    persist(st)
    broadcast_now(st["id"], {"type": "state", "state": public_state(st)})
    return {"sid": st["id"], "token": token, "state": public_state(st)}

--- lobby_start ---
def lobby_start(sid: str, token: str):
    st = get_state(sid)
    if not st:
        raise HTTPException(404)
    if st["tokens"].get(st["order"][0]) != token:
        raise HTTPException(403, "Только хост может начать игру")
    st["status"] = "playing"
    persist(st)
    broadcast_now(sid, {"type": "state", "state": public_state(st)})
    return {"ok": True, "state": public_state(st)}

--- ws_endpoint ---
async def ws_endpoint(websocket: WebSocket, sid: str,
                      player: str = None, token: str = None):
    st = get_state(sid)
    if not st:
        await websocket.close(code=4004)
        return
    if st.get("tokens") and token:
        if st["tokens"].get(player) != token:
            await websocket.close(code=4003)
            return
    await manager.connect(sid, websocket, player or "spectator")
    try:
        await websocket.send_json({"type": "state", "state": public_state(st)})
        while True:
            await websocket.receive_text()  # ping от клиента
    except WebSocketDisconnect:
        manager.disconnect(sid, websocket)

--- get_state ---
def get_state(sid):
    st = SESSIONS.get(sid)
    if st is None:
        st = db.load_session(sid)
        if st:
            SESSIONS[sid] = st
    return st

--- persist ---
def persist(st):
    SESSIONS[st["id"]] = st
    db.save_session(st["id"], st)

--- public_state ---
def public_state(st):
    """Состояние без секретов (токены не отдаём клиентам)."""
    return {k: v for k, v in st.items() if k != "tokens"}

--- broadcast_now ---
def broadcast_now(sid, message):
    if LOOP is None:
        print(f"[WARN] broadcast пропущен: LOOP is None (sid={sid})")
        return
    if not manager.conns.get(sid):
        print(f"[WARN] broadcast пропущен: нет WS-подключений (sid={sid})")
        return
    asyncio.run_coroutine_threadsafe(manager.broadcast(sid, message), LOOP)


===== backend/engine.py =====

--- resolve_check ---
def resolve_check(state, actor, judge):
    """Обрабатывает действие игрока. Числа и модификаторы — из data/rules (книга)."""
    if judge.get("action_type") == "free":
        return {
            "dice": None, "die_total": None, "stat": None, "skill": None,
            "mods": 0, "total": None, "dv": None, "success": True,
            "margin": 0, "critical": False, "fumble": False,
            "actor": actor["name"], "action_type": "free",
            "skill": "", "stat_key": None, "dv_key": None, "no_roll": True,
        }

    at = judge.get("action_type", "skill")
    target = _find_target(state, actor, judge, at)

    dv_table = rules.get("combat", "dv_table", house=DV)
    dv_key = judge.get("dv_key", "everyday")
    dv = judge.get("dv") or dv_table.get(dv_key, 13)

    skill = judge.get("skill") or ""
    stat_key = SKILL_STAT.get(skill, judge.get("stat", "COOL"))
    book_skills = rules.get_optional("creation", "skill_list")
    if isinstance(book_skills, list):
        mapped = {s["key"]: s["stat"] for s in book_skills
                  if isinstance(s, dict) and s.get("key") and s.get("stat")}
        stat_key = mapped.get(skill, stat_key)
    elif isinstance(book_skills, dict):
        stat_key = book_skills.get(skill, stat_key)
    stat = actor["stats"].get(stat_key, 2)
    sk_lvl = actor["skills"].get(skill, 0)

    wound_state = get_wound_state(actor.get("hp", actor.get("max_hp", 10)),
                                  actor.get("max_hp", 10))
    wound_pen = rules.get_optional("combat", "wound_penalties")
    mods = wound_pen.get(wound_state, 0) if isinstance(wound_pen, dict) else get_wound_penalty(wound_state)
    armor_rec = ARMOR.get(actor.get("armor") or "", {}) or {}
    armor_pen = int(armor_rec.get("penalty", 0) or 0)
    pen_stats = armor_rec.get("penalty_stats") or ["REF", "DEX", "MOVE"]
    if armor_pen and stat_key in pen_stats:
        mods += armor_pen

    location = (judge.get("location") or "auto")
    aimed_pen = 0
    if at in ("attack_ranged", "attack_melee"):
        penalties = _crule("aimed_shot_penalties") or {}
        aimed_pen = int(penalties.get(location, 0))
        mods += aimed_pen

    mech = skill_check(stat, sk_lvl, dv, mods)
    mech["armor_penalty"] = armor_pen if stat_key in pen_stats else 0
    mech.update({
        "actor": actor["name"], "action_type": at, "skill": skill,
        "stat_key": stat_key, "dv_key": dv_key,
        "wound_state": wound_state, "wound_penalty": wound_pen if isinstance(wound_pen, dict) else mods,
        "location": location, "aimed_penalty": aimed_pen,
    })

    if at == "attack_ranged" and not judge.get("weapon"):
        judge["weapon"] = "heavy_pistol"
    if at == "attack_melee" and not judge.get("weapon"):
        judge["weapon"] = "knife"

    # === ТРАНСПОРТ ===
    if at == "drive":
        vehicle_key = actor.get("vehicle")
        if not vehicle_key:
            mech.update({"drive_result": "no_vehicle", "reason": "Персонаж не в транспорте"})
            return mech
        from . import vehicles as veh_mod
        v = veh_mod.get_vehicle(vehicle_key)
        mech.update({"drive_result": "maneuver", "vehicle": vehicle_key,
                     "vehicle_name": (v or {}).get("name", vehicle_key)})

    if at == "ram":
        attacker_vehicle = actor.get("vehicle")
        if not attacker_vehicle:
            mech.update({"ram_result": "no_vehicle", "reason": "Персонаж не в транспорте"})
            return mech
        from . import vehicles as veh_mod
        target_vehicle = (target or {}).get("vehicle")
        dmg = veh_mod.ram_damage(attacker_vehicle, target_vehicle or "car_compact")
        mech.update({
            "ram_result": "hit" if mech["success"] else "miss",
            "ram_raw": dmg["raw"], "ram_sp": dmg["sp"],
            "ram_net": dmg["net"] if mech["success"] else 0,
            "target": (target or {}).get("name"),
        })
        if target is not None and mech["success"] and dmg["net"] > 0:
            dr = apply_damage(target, dmg["net"])
            target["hp"] = dr["hp"]
            target["wound"] = dr["wound_state"]
            mech["target_hp"] = target["hp"]
            mech["target_wound"] = target["wound"]
            mech["target_id"] = target["id"]

    # === НЕТРАННИНГ ===
    if at == "hack":
        cyberware = actor.get("cyberware", [])
        if not any("interface" in c.lower() for c in cyberware):
            mech.update({"hack_result": "no_interface",
                         "reason": "Нет Interface Plugs для входа в сеть"})
            return mech
        if mech["success"]:
            arch_key = judge.get("architecture", "simple")
            net_state = netrunning.enter_architecture(actor, arch_key)
            if net_state["success"]:
                mech.update({"hack_result": "entered", "architecture": arch_key,
                             "floor": 1, "max_floors": net_state["max_floors"],
                             "net_dv": net_state["dv"]})
            else:
                mech.update({"hack_result": "failed",
                             "reason": net_state.get("reason", "Не удалось войти")})
        else:
            mech.update({"hack_result": "failed_check", "reason": "Провал проверки interface"})

    # === УРОН ===
    if at in ("attack_ranged", "attack_melee") and mech["success"]:
        wkey = judge.get("weapon", "heavy_pistol" if at == "attack_ranged" else "knife")
        move_key = judge.get("move")
        w = WEAPONS.get(wkey, {"damage": "2d6"})

        dmg, faces = roll_dice(w.get("damage", "2d6"))
        sixes = sum(1 for f in faces if f == 6)
        crit = sixes >= int(_crule("critical_injury_trigger") or 2)

        mults = _crule("aimed_shot_multipliers") or {}
        mult = float(mults.get(location, 1))
        raw = int(round(dmg * mult))

        sp = armor_sp(target) if target else 0
        net = max(0, raw - sp)

        martial_effect = None
        martial_effect_desc = ""
        if move_key and move_key in martial.MOVES:
            net = martial.apply_move_bonus(move_key, net)
            martial_effect, martial_effect_desc = martial.get_move_effect(move_key)

        bonus = int(_crule("critical_injury_bonus") or 0) if crit else 0
        total_damage = net + bonus

        mech.update({
            "weapon": wkey, "damage_roll": faces, "damage": dmg,
            "damage_multiplier": mult, "damage_after_multiplier": raw,
            "armor_sp": sp, "net_damage": net, "bonus_damage": bonus,
            "total_damage": total_damage, "target": (target or {}).get("name"),
            "critical_success": crit, "martial_move": move_key,
            "martial_effect": martial_effect, "martial_effect_desc": martial_effect_desc,
        })

        if target is not None:
            mech["target_id"] = target["id"]
            abl = ablate_armor(target, raw > sp)
            if abl:
                mech["armor_ablation"] = abl
            if total_damage > 0:
                dr = (apply_damage(target, total_damage, weapon_key=wkey, crit=crit)
                      if _ACCEPTS_CRIT else apply_damage(target, total_damage, weapon_key=wkey))
                target["hp"] = dr["hp"]
                target["wound"] = dr["wound_state"]
                target["wound_penalty"] = dr["penalty"]
                injury = dr.get("critical_injury")
                if injury and crit:
                    mech["critical_injury"] = injury
                elif injury and not crit:
                    mech["injury_suppressed"] = injury  # не подтверждено кубиками — не объявляем критом
                if dr.get("death_save"):
                    death_result = death_save(target)
                    target["dead"] = death_result["dead"]
                    mech["death_save"] = death_result
                    if death_result["dead"]:
                        mech["target_dead"] = True
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

--- _is_hostile ---
def _is_hostile(npc):
    """Враждебен ли NPC (боец охраны и т.п.)."""
    name = (npc.get("name") or "").lower()
    return any(k in name for k in HOSTILE_KEYWORDS)

--- _npc_weapon_key ---
def _npc_weapon_key(npc):
    name = (npc.get("name") or "").lower()
    if any(k in name for k in ("телохранитель", "охранник", "солдат", "боевик")):
        return "heavy_pistol"
    return "medium_pistol"


===== backend/creation.py =====

--- ROLE_ALIASES ---
ROLE_ALIASES = {
    "techie": "Tech", "tech": "Tech", "netrunner": "Netrunner", "solo": "Solo",
    "rockerboy": "Rockerboy", "fixer": "Fixer", "nomad": "Nomad",
    "medtech": "Medtech", "lawman": "Lawman", "exec": "Exec", "media": "Media",
}

--- ROLES ---
NOT FOUND

--- STATS ---
NOT FOUND

--- SKILLS ---
NOT FOUND

--- GEAR ---
NOT FOUND

--- PROGRAMS ---
NOT FOUND

--- ROLE_PRESETS ---
ROLE_PRESETS = {
    "Solo":      {"stats": {"INT": 3, "REF": 7, "DEX": 5, "TECH": 3, "COOL": 5, "WILL": 4, "LUCK": 2, "MOVE": 5, "BODY": 6, "EMP": 3},
                  "skills": {"handgun": 4, "melee_weapon": 3, "evasion": 3, "athletics": 3, "perception": 3},
                  "weapon": "heavy_pistol", "armor": "light_armorjack",
                  "gear": ["armored_jacket", "knife"], "cyber": ["Neural Link"], "programs": []},
    "Netrunner": {"stats": {"INT": 6, "REF": 4, "DEX": 3, "TECH": 5, "COOL": 4, "WILL": 4, "LUCK": 3, "MOVE": 4, "BODY": 4, "EMP": 4},
                  "skills": {"interface": 4, "programming": 3, "stealth": 3, "perception": 2, "electronics_security_tech": 2},
                  "weapon": "medium_pistol", "armor": "leathers",
                  "gear": ["cyberdeck", "agent"], "cyber": ["Neural Link", "Interface Plugs"],
                  "programs": ["sword", "armor", "seeya"]},
    "Tech":      {"stats": {"INT": 5, "REF": 4, "DEX": 4, "TECH": 7, "COOL": 4, "WILL": 4, "LUCK": 3, "MOVE": 4, "BODY": 4, "EMP": 4},
                  "skills": {"basic_tech": 4, "weaponstech": 3, "electronics_security_tech": 3, "perception": 2},
                  "weapon": "medium_pistol", "armor": "leathers",
                  "gear": ["toolkit", "lockpick"], "cyber": ["Neural Link"], "programs": []},
}

--- normalize_role ---
def normalize_role(role):
    roles = _book("roles")
    if not role:
        return random.choice(roles)
    r = ROLE_ALIASES.get(str(role).strip().lower(), "Solo")
    return r if r in roles else roles[0]

--- preset ---
def preset(role):
    r = normalize_role(role)
    return ROLE_PRESETS.get(r, _DEFAULT), r

--- random_character ---
def random_character(role=None, name=None):
    p, r = preset(role)
    return _finalize(name or random.choice(HANDLES), r, p["stats"], p["skills"],
                     p["weapon"], p["armor"], p["gear"], p["cyber"], p["programs"])

--- options ---
def options(role=None):
    p, r = preset(role)
    lim = limits()
    skill_list = _book("skill_list")
    return {
        "role": r, "roles": _book("roles"),
        "stats": _book("stat_list"),
        "stat_min": lim["stat_min"], "stat_max": lim["stat_max"], "stat_pool": lim["stat_pool"],
        "skills": [s["key"] if isinstance(s, dict) else s for s in skill_list],
        "skill_stat": {s["key"]: s["stat"] for s in skill_list if isinstance(s, dict)},
        "skill_pool": lim["skill_pool"], "skill_max": lim["skill_max"],
        "gear": _book("gear"), "gear_limit": lim["gear_limit"],
        "weapons": _book("weapons"), "armors": _book("armors"),
        "programs": _book("programs"), "prog_limit": lim["prog_limit"],
        "preset": p,
        "sources": _sources(["roles", "stat_list", "stat_min", "stat_max",
                             "stat_pool_edgerunner", "skill_pool_edgerunner",
                             "skill_max_at_creation", "skill_list", "starting_eb"]),
        "house_keys": sorted(k for k, v in rules.house_hits().items() if v is not None),
    }

--- build ---
def build(spec):
    lim = limits()
    role = normalize_role(spec.get("role"))
    stat_keys = _book("stat_list")
    stats = {k: int(spec.get("stats", {}).get(k, lim["stat_min"])) for k in stat_keys}
    if any(not (lim["stat_min"] <= v <= lim["stat_max"]) for v in stats.values()):
        raise ValueError(f"статы вне диапазона {lim['stat_min']}..{lim['stat_max']}")
    if sum(stats.values()) > lim["stat_pool"]:
        raise ValueError(f"пул статов превышен (макс {lim['stat_pool']})")
    allowed = {s["key"] if isinstance(s, dict) else s for s in _book("skill_list")}
    skills = {k: int(v) for k, v in (spec.get("skills") or {}).items()
              if int(v) > 0 and k in allowed}
    if any(v > lim["skill_max"] for v in skills.values()):
        raise ValueError(f"навык выше лимита создания {lim['skill_max']}")
    if sum(skills.values()) > lim["skill_pool"]:
        raise ValueError(f"пул навыков превышен (макс {lim['skill_pool']})")
    gear = [g for g in (spec.get("gear") or []) if g in _book("gear")][:lim["gear_limit"]]
    weapon = spec.get("weapon") if spec.get("weapon") in _book("weapons") else "medium_pistol"
    armor = spec.get("armor") if spec.get("armor") in _book("armors") else "leathers"
    programs = [p for p in (spec.get("programs") or []) if p in _book("programs")][:lim["prog_limit"]]
    cyber = ["Neural Link"]
    if role == "Netrunner":
        cyber.append("Interface Plugs")
        if "cyberdeck" not in gear:
            gear.append("cyberdeck")
    return _finalize(spec.get("name") or random.choice(HANDLES), role, stats, skills,
                     weapon, armor, gear, cyber, programs)


===== static/index.html =====

--- renderLogEntry ---
function renderLogEntry(e) {
  addLog(`${e.player}: ${e.text}`, 'mech');
  const m = e.mech || {};
  if (m.no_roll) addLog('[без броска] свободное действие', 'mech');
  else if (m.action_type) {
    const loc = (m.location && m.location !== 'auto') ? ` [${LOCATION_RU[m.location] || m.location}]` : '';
    addLog(`[механика] ${m.action_type}${loc} | ${m.stat_key}+${m.skill}: ${m.total} vs DV${m.dv} -> ${m.success ? 'УСПЕХ' : 'ПРОВАЛ'}`, 'mech');
  }
  if (m.assist) addLog(`[помощь] +${m.assist.bonus || 0}`, 'mech');
  if (m.damage != null) addLog(`цель ${m.target}: урон ${m.damage} - SP${m.armor_sp} = ${m.net_damage}`, 'mech');
  if (m.critical_injury) addLog(`[критическая травма у ${m.target || 'цели'}] ${m.critical_injury}`, 'mech');
  if (m.npc_reaction) {
    const nr = m.npc_reaction;
    (nr.shots || [nr]).forEach(s => {
      addLog(`[ответ NPC] ${s.npc} → ${nr.target_player || 'игрок'}: ${s.success ? 'попадание' : 'промах'}, урон ${s.net_damage || 0}`, 'mech');
      if (s.critical_injury) addLog(`[критическая травма у игрока] ${s.critical_injury}`, 'mech');
    });
    if (nr.principal) addLog(`[NPC] ${nr.principal.npc}: ${nr.principal.text}`, 'mech');
  }
  if (e.narration) addLog(e.narration, 'narr');
}

--- syncLog ---
function syncLog() {
  const log = (currentState && currentState.log) || [];
  for (let i = renderedLogCount; i < log.length; i++) renderLogEntry(log[i]);
  renderedLogCount = log.length;
}

--- connectWS ---
function connectWS() {
  if (ws) { ws.onclose = null; try { ws.close(); } catch (e) {} }
  if (e.code === 4003) {
      localStorage.removeItem('tok_' + sid);
      localStorage.removeItem('me_' + sid);
      showErr('err', 'WS: токен устарел — выйдите в меню и войдите в комнату заново');
    }  
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${proto}//${location.host}/ws/${sid}?player=${encodeURIComponent(myName || '')}&token=${token || ''}`;
  ws = new WebSocket(url);
  ws.onopen = () => { console.log('[WS] connected'); setWsDot(true); };
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'state') {
      currentState = msg.state;
      if (currentState.status === 'playing') {
        if (document.getElementById('game').classList.contains('hidden')) enterGame(currentState);
        else { syncLog(); renderAll(); }
      } else {
        updateWaitingList();
      }
    }
  };
  ws.onclose = (e) => {
    console.log('[WS] closed, code:', e.code);
    setWsDot(false);
    if (e.code === 4003) showErr('err', 'WS: неверный токен игрока');
    if (e.code === 4004) showErr('err', 'WS: сессия не найдена');
    if (mode === 'online' && sid && e.code !== 4003 && e.code !== 4004) {
      setTimeout(connectWS, 3000);  // автопереподключение
    }
  };
  ws.onerror = () => console.log('[WS] error');
}

--- send ---
async function send() {
  if (busy || !sid) return;
  const actorName = activeName();
  if (mode === 'online' && myName !== actorName) {
    showErr('err', 'Сейчас не ваш ход');
    return;
  }
  const action = document.getElementById('action').value.trim();
  if (!action) return;
  const assistVal = document.getElementById('assist').value || null;
  busy = true;
  document.getElementById('sendbtn').disabled = true;
  document.getElementById('busy-note').classList.remove('hidden');
  document.getElementById('err').textContent = '';
  document.getElementById('action').value = '';
  addLog(`${actorName}: ${action}`, 'mech', true);
  try {
    const body = {player: actorName, text: action};
    if (assistVal) body.assist = assistVal;
    if (mode === 'online') body.token = token;
    const r = await fetch(`/session/${sid}/action`, {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail || `HTTP ${r.status}`); }
    const d = await r.json();
    if (!d || typeof d !== 'object') throw new Error('Пустой ответ сервера');
    lastTurnId = d.turn_id;
    if (d.state) currentState = d.state;
    if (mode === 'local') currentPlayer = d.next_player;
    document.querySelectorAll('[data-echo]').forEach(el => el.remove());
    syncLog();
    renderAll();
    if (lastTurnId) { document.getElementById('rating').classList.remove('hidden'); resetStars(); }
  } catch (e) {
    document.querySelectorAll('[data-echo]').forEach(el => el.remove());
    showErr('err', 'Ошибка: ' + e.message);
  } finally {
    busy = false;
    document.getElementById('busy-note').classList.add('hidden');
    renderAll();
  }
}

--- cbLoad ---
async function cbLoad() {
  const role = document.getElementById('cb-role').value || null;
  CB = await (await fetch('/creation/options' + (role ? '?role=' + role : ''))).json();
  CB.spec = {
    role: CB.role,
    stats: Object.assign({}, CB.preset.stats),
    skills: Object.assign({}, CB.preset.skills),
    gear: CB.preset.gear.slice(), weapon: CB.preset.weapon,
    armor: CB.preset.armor, programs: CB.preset.programs.slice(),
  };
  document.getElementById('cb-weapon').innerHTML = CB.weapons.map(w => `<option ${w===CB.spec.weapon?'selected':''}>${w}</option>`).join('');
  document.getElementById('cb-armor').innerHTML = CB.armors.map(a => `<option ${a===CB.spec.armor?'selected':''}>${a}</option>`).join('');
  document.getElementById('cb-gear-limit').textContent = CB.gear_limit;
  document.getElementById('cb-prog-limit').textContent = CB.prog_limit;
  cbRender();
}

--- cbBuild ---
async function cbBuild() {
  CB.spec.weapon = document.getElementById('cb-weapon').value;
  CB.spec.armor = document.getElementById('cb-armor').value;
  CB.spec.name = document.getElementById('cs-name').textContent;
  const r = await fetch('/creation/build', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(CB.spec)});
  if (!r.ok) { const e = await r.json().catch(()=>({})); alert(e.detail || 'Ошибка сборки'); return; }
  pendingChar = await r.json();
  renderCharPreview();
}

--- confirmChar ---
async function confirmChar() {
  if (!pendingChar) return alert('Сначала сгенерируйте или соберите персонажа');
  const name = document.getElementById('cs-name').textContent;
  const m = pendingMode, code = pendingCode, char = pendingChar;
  char.name = name;
  closeCharSelect();
  if (m === 'join') await doJoin(code, name, char);
  else await doCreate(name, char, m === 'solo');
}

--- doCreate ---
async function doCreate(name, char, solo) {
  try {
    const resp = await fetch('/lobby/create', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({player_name: name, character: char})});
    if (!resp.ok) {
      const e = await resp.json().catch(() => ({}));
      showErr('host-err', e.detail || 'Ошибка');
      return;
    }
    const data = await resp.json();
    mode = 'online';
    sid = data.sid; token = data.token; myName = name;
    localStorage.setItem('sid', sid);
    localStorage.setItem('tok_' + sid, token);
    localStorage.setItem('me_' + sid, name);
    currentState = data.state;
    if (solo) { await startOnline(); return; }
    document.getElementById('room-code').textContent = data.code;
    document.getElementById('waiting-box').classList.remove('hidden');
    document.getElementById('start-btn').classList.remove('hidden');
    updateWaitingList();
    connectWS();
  } catch (e) {
    console.error(e);
    showErr('host-err', 'Ошибка: ' + e.message);
  }
}

--- doJoin ---
async function doJoin(code, name, char) {
  try {
    const resp = await fetch('/lobby/join', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({code: code, player_name: name, character: char})});
    if (!resp.ok) {
      const e = await resp.json().catch(() => ({}));
      showErr('join-err', e.detail || 'Ошибка');
      return;
    }
    const data = await resp.json();
    mode = 'online';
    sid = data.sid; token = data.token; myName = name;
    localStorage.setItem('sid', sid);
    localStorage.setItem('tok_' + sid, token);
    localStorage.setItem('me_' + sid, name);
    currentState = data.state;
    document.getElementById('waiting-box').classList.remove('hidden');
    document.getElementById('room-code').textContent = code;
    updateWaitingList();
    connectWS();
  } catch (e) {
    console.error(e);
    showErr('join-err', 'Ошибка: ' + e.message);
  }
}
