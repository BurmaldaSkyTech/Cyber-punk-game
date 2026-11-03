# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid, json, os
from pathlib import Path

from . import db, engine, scenario, chargen
from .llm import chat_json
from .rag import RulesSearch
from .common import clean, CJK

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC = Path(__file__).resolve().parent.parent / "static"
STATIC.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC), name="static")

SEARCH = RulesSearch()
SESSIONS = {}

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "qwen2.5:7b-instruct")
NARR_MODEL = os.environ.get("NARR_MODEL", "qwen2.5:14b")

ACTION_LABEL = {
    "attack_ranged": "выстрел / огнестрельное оружие",
    "attack_melee": "физическая атака / ближний бой",
    "hack": "взлом или нетраннинг",
    "social": "социальное воздействие: речь, ложь, убеждение",
    "skill": "проверка навыка (скрытность, восприятие и т.п.)",
    "heal": "лечение",
    "free": "свободное действие без броска",
}

CONTRACT_BEATS = [
    "ЦЕЛЬ: крио-капсула с нейроимплантом 'Лазарь' в дата-узле Biotechnica, промзона, sector 7.",
    "ОХРАНА: 4 guard в kevlar + сержант в heavy armorjack; патрули ходят по расписанию, смены каждые 2 часа.",
    "СЛАБОЕ МЕСТО: служебный вход с кодовым замком и слепая зона камер у северного забора.",
    "УСЛОВИЕ: имплант нужен ЦЕЛЫМ; капсулу не вскрывать до передачи Кесслеру лично в руки.",
    "СРОК: до рассвета — после смены охраны в 06:00 доступ к узлу закроется.",
]
CONTRACT_GEAR = ["assault_rifle", "smg", "cam_jammer", "fake_pass", "medkit", "grapnel"]

ACT2_TRIGGERS = [
    "отправляемся", "выдвигаемся", "пора на дело", "идём на дело",
    "едем на дело", "на задание", "пора работать", "хватит болтать",
    "встаёт", "идёт к выходу", "поднимается", "направляется к двери",
    "покидает бар", "уходит", "заканчивает разговор", "прощается"
]

JUDGE_SYS = """Ты — механический интерпретатор правил Cyberpunk RED. Никакой прозы, только JSON:
{"action_type": "skill|attack_ranged|attack_melee|hack|social|heal|free",
 "skill": "ключ навыка строго из списка персонажа или null",
 "dv_key": "simple|everyday|difficult|professional|heroic|incredible|legendary или null",
 "weapon": "ключ оружия или null", "target": "id NPC или null",
 "second": null или такой же объект для ВТОРОЙ части составного действия,
 "query": "короткий запрос для поиска правил или null"}

=== ПРИОРИТЕТЫ (проверяй СНАЧАЛА, сверху вниз) ===

1. АТАКА: выстрел, удар, бросок гранаты → attack_ranged / attack_melee.
2. ВЗЛОМ: сеть, электроника, замки, камеры → hack или skill.
3. СОЦИАЛКА (если есть ЛЮБОЕ из): обращение к NPC по имени, просьба ("дай", "одолжи", "можно", "разреши", "покажи", "расскажи"), вопрос NPC ("расскажи", "объясни", "а что если"), убеждение, торг, ложь, лесть → social.
   ВАЖНО: если игрок говорит "дай X и мы пойдём" / "одолжи Y на дело" / "покажи контракт" — это ВСЁ ЕЩЁ social, потому что главное — просьба/приказ, а "пойдём" лишь аргумент.
4. НАВЫК: скрытность, акробатика, вождение, поиск, медицина и т.п. без обращения к NPC → skill.
5. FREE (без броска): ТОЛЬКО если фраза — чистое описание состояния или команда без обращения к NPC.
   Примеры free: "Сидит на стуле", "Стоит у стены", "Пропускаю ход", "Жду", "Отправляемся", "Встаю и иду к выходу".
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

dv_key: тривиально -> everyday; настороже -> difficult; защита -> professional; на грани -> heroic.
skill строго из списка персонажа.
Верни ТОЛЬКО JSON."""

NARR_SYS = """Ты — игровой мастер текстовой киберпанк-настолки. Пиши СТРОГО на русском, без латинских и иероглифических букв внутри слов.
Жанр: мрачный неонуар, короткая жёсткая проза. Запрещены штампы "в воздухе витает", "запах коррозии и тайны".
ПРАВИЛА:
1. Третье лицо о персонаже игрока: "Вектор сделал", "Никс успела". Никаких "ты/ваш".
2. Начни прямо с результата заявленного действия, не пересказывай сцену.
3. УСПЕХ/ПРОВАЛ бери из РЕЗУЛЬТАТА. Если в ПОСЛЕДСТВИЯХ сказано "броня поглотила весь урон" — НЕТ раны и крови: описывай удар, искры, отдачу, контузию, но цель НЕ ранена.
4. ЗАПРЕЩЕНО копировать фразы из ПРИМЕРОВ и из блока ПРЕДЫДУЩИЕ ХОДЫ: каждый ход — новый кадр и новые формулировки.
5. Запрещено вводить персонажей, банды и события, которых нет в СЦЕНЕ и ФАКТАХ. ЛОР — только названия и детали.
6. Описывай только те изменения состояния NPC, которые есть в ПОСЛЕДСТВИЯХ.
7. Числа урона, HP, DV — только из ФАКТОВ.
8. Объём 3–5 предложений, затем 1–2 вопроса и 2–4 варианта инфинитивом.
9. РЕАКЦИЯ NPC: если игрок успешно атакует или взламывает NPC, NPC активно реагирует: отбивается, уклоняется, контратакует, зовёт подмогу. Пассивное поведение запрещено.
10. FREE-ДЕЙСТВИЯ: если РЕЗУЛЬТАТ = "НЕЙТРАЛЬНО (без броска)", НЕ пиши про успех/провал/бросок. Описывай просто действие и атмосферу.
11. АНТИ-ПОВТОР: НЕ начинай два хода подряд с одного и того же жеста или фразы NPC. Меняй фокус кадра.
12. Имя персонажа — СУЩЕСТВИТЕЛЬНОЕ. Никогда не используй имя как глагол.

ПРИМЕРЫ (копировать их фразы запрещено):
ФАКТЫ: действие "незаметно дёрнуть флешку", ПРОВАЛ, margin -2
НАРРАТИВ: "Локоть курьера в последний момент уходит в сторону — пальцы смыкаются на пустой ткани. Он резко оборачивается, прижимая флешку к груди, и его глаза мечутся в поисках охраны."
ФАКТЫ: действие "выстрелить в охранника", УСПЕХ, net_damage 0, armor_sp 7
НАРРАТИВ: "Пуля заставляет охранника дёрнуться, но тяжёлый armorjack лишь щёлкает под ударом: пластина держит. Он ныряет за прилавок и хрипло кричит что-то в рацию."

Верни только JSON:
{"narration": str, "questions": [str], "choices": [str],
 "safe_state_suggestions": {"heat_delta": -1|0|1, "add_flags": [str], "clock_progress": {name: 0|1|2}, "npc_action": str}}"""

NARR_SYS_UNIVERSAL = """Ты — игровой мастер текстовой киберпанк-настолки. Пиши СТРОГО на русском, без латинских и иероглифических букв внутри слов.
Жанр: мрачный неонуар, короткая жёсткая проза.

=== ФОРМАТ: СЛОВА И ДЕЙСТВИЯ ===

Разделяй речь и действия персонажей:
- Речь — обычным текстом.
- Действия — в *звёздочках*.
- Пример: "Ублюдки, вам меня не взять *кидает гранату*"
- НЕ пиши действия без звёздочек и не смешивай их с речью в одном предложении.

=== КРИТИЧЕСКИЕ ЗАПРЕТЫ ===

0. **НИКАКИХ "ТЫ/ТВОЙ/ТЕБЯ"** — это главное правило. Всегда третье лицо.
1. НИКОГДА не придумывай новые локации, фракции, кланы, города или сюжетные повороты. Используй ТОЛЬКО то, что есть в блоках РАСКРОЙ ФАКТ и УЖЕ РАСКРЫТО.
2. НЕ повторяй жесты и фразы из ПРЕДЫДУЩИЕ ХОДЫ. Если в прошлом ходу персонаж "налил виски" — в этом ходу он делает ЧТО-ТО ДРУГОЕ.
3. НЕ добавляй условия сделки, если их нет в РАСКРОЙ ФАКТ.
4. НЕ используй имя персонажа как глагол.

=== ПРАВИЛА НАРРАЦИИ ===

1. **СТРОГО ТРЕТЬЕ ЛИЦО.** Используй только имя персонажа игрока ("Вектор сделал", "Никс успела") или "он"/"она"/"они". **КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНЫ** обращения "ты", "твой", "тебя", "тебе", "ваш", "ваше" в описаниях.
   ❌ НЕПРАВИЛЬНО: "Ты входишь в бар", "Твоя рука тянется", "Он смотрит тебе прямо в глаза"
   ✅ ПРАВИЛЬНО: "Вектор входит в бар", "Его рука тянется", "Он смотрит Вектору прямо в глаза"
   Если имя персонажа — "1" или другое неестественное, используй его как есть в третьем лице.

2. Начни прямо с результата заявленного действия, не пересказывай сцену.

3. УСПЕХ/ПРОВАЛ бери из РЕЗУЛЬТАТА. Если в ПОСЛЕДСТВИЯХ сказано "броня поглотила весь урон" — НЕТ раны и крови: описывай удар, искры, отдачу, но цель НЕ ранена.

4. ЗАПРЕЩЕНО копировать фразы из ПРИМЕРОВ и из блока ПРЕДЫДУЩИЕ ХОДЫ: каждый ход — новый кадр и новые формулировки.

5. Запрещено вводить персонажей, банды и события, которых нет в СЦЕНЕ и ФАКТАХ.

6. Числа урона, HP, DV — только из ФАКТОВ.

7. Объём 3–5 предложений, затем 1–2 вопроса и 2–4 варианта инфинитивом.

8. РЕАКЦИЯ ПЕРСОНАЖЕЙ: все персонажи в сцене активно реагируют. Если игрок успешно атакует — цель отбивается, уклоняется, контратакует, зовёт подмогу. Пассивное поведение запрещено.

9. УСПЕХ социального действия: персонаж раскрывает факт из РАСКРОЙ ФАКТ. ПРОВАЛ: уклоняется, но даёт ОДНУ зацепку.

10. Если игрок просит снаряжение и УСПЕХ — персонаж физически передаёт предмет: опиши жест передачи и добавь в grant_items.

11. FREE-ДЕЙСТВИЯ (РЕЗУЛЬТАТ "НЕЙТРАЛЬНО"): без успеха/провала, просто сцена и атмосфера.

=== ПРАВИЛЬНЫЕ ПРИМЕРЫ (копировать запрещено) ===

РАСКРОЙ ФАКТ: "ЦЕЛЬ: крио-капсула с нейроимплантом 'Лазарь' в дата-узле Biotechnica, промзона, sector 7."
УСПЕХ: "Кесслер стряхивает пепел и наклоняется ближе: 'Биотехника, сектор 7. Там крио-капсула с имплантом Лазарь. Стоит баснословных денег.' *кивает на планшет*"

РАСКРОЙ ФАКТ: "ОХРАНА: 4 guard в kevlar + сержант в heavy armorjack"
УСПЕХ: "Он барабанит пальцами по столу: 'Четыре охранника в кевларе, плюс сержант в тяжёлой броне. Меняются каждые два часа.'"

ПРОВАЛ: "Кесслер усмехается: 'Охрана? Ну, скажем так, там не пустые коридоры. Но детали — после аванса.'"

НЕ ДЕЛАЙ ТАК:
❌ "это подлинные данные об опасной миссии по взлому в Новом Сент-Джеймсе" — локация должна быть из РАСКРОЙ ФАКТ
❌ "проблемы с местным кланом Королевских" — не выдумывай фракции

Верни только JSON:
{"narration": str, "questions": [str], "choices": [str],
 "safe_state_suggestions": {"heat_delta": -1|0|1, "add_flags": [str],
  "grant_items": [str из списка: assault_rifle, smg, cam_jammer, fake_pass, medkit, grapnel],
  "npc_action": str}}"""


class NewSession(BaseModel):
    players: list
    scenario: dict


class ActionIn(BaseModel):
    player: str
    text: str
    assist: Optional[str] = None


class RateIn(BaseModel):
    rating: int
    edited: Optional[str] = None


class ChargenIn(BaseModel):
    mode: str = "random"
    role: Optional[str] = None
    seed: Optional[int] = None
    manual: Optional[dict] = None


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/setup")
def setup_page():
    return FileResponse(STATIC / "setup.html")


@app.post("/chargen")
def chargen_endpoint(req: ChargenIn):
    if req.mode == "manual":
        ch, problems = chargen.manual_character(req.manual or {})
        if problems:
            raise HTTPException(400, detail=problems)
        role = ch.get("role")
        if role in chargen.ROLES:
            rd = chargen.ROLES[role]
            ch.setdefault("cyberware", rd["starting_cyberware"])
            ch.setdefault("eb", chargen.STARTING_EB[role])
            ch.setdefault("weapon", rd["weapon"])
            ch.setdefault("armor", rd["armor"])
            ch.setdefault("gear", rd["items"])
            ch.setdefault("ability", rd["ability"])
        return ch
    return chargen.random_character(role=req.role, seed=req.seed)


@app.post("/chargen/validate")
def chargen_validate(req: dict):
    role = req.get("role")
    if role in chargen.ROLES:
        rd = chargen.ROLES[role]
        req.setdefault("cyberware", rd["starting_cyberware"])
        req.setdefault("eb", chargen.STARTING_EB[role])
        req.setdefault("weapon", rd["weapon"])
        req.setdefault("armor", rd["armor"])
        req.setdefault("gear", rd["items"])
        req.setdefault("ability", rd["ability"])
    _, problems = chargen.manual_character(req)
    return {"valid": len(problems) == 0, "problems": problems}


@app.post("/session")
def new_session(req: NewSession):
    sid = uuid.uuid4().hex[:8]
    base = scenario.init_scenario()
    SESSIONS[sid] = {
        "id": sid, "scenario": req.scenario,
        "heat": req.scenario.get("heat", 0),
        "clocks": req.scenario.get("clocks", {}),
        "flags": [], "log": [], "turn": 0, "threat": None,
        "order": [p["name"] for p in req.players],
        "players": req.players, "npcs": req.scenario.get("npcs", []),
        "revealed_beats": [], "granted": [],
        **base,
    }
    return {"id": sid, "state": SESSIONS[sid]}


@app.get("/session/{sid}")
def get_session(sid: str):
    if sid not in SESSIONS:
        raise HTTPException(404)
    return SESSIONS[sid]


def clamp_suggestions(s, st):
    s = s or {}
    hd = max(-1, min(1, int(s.get("heat_delta", 0) or 0)))
    flags = []
    for f in (s.get("add_flags") or [])[:2]:
        f = str(f)
        if f not in st["flags"] and f not in flags:
            flags.append(f)
    clocks = {k: max(0, min(2, int(v))) for k, v in (s.get("clock_progress") or {}).items()}
    npc_action = s.get("npc_action") or ""
    grants = []
    for g in (s.get("grant_items") or [])[:2]:
        g = str(g)
        if g in CONTRACT_GEAR and g not in st.get("granted", []):
            grants.append(g)
    return {"heat_delta": hd, "add_flags": flags, "clock_progress": clocks,
            "npc_action": npc_action, "grant_items": grants}


def consequences(mech):
    cons = []
    items = [mech] + ([mech["second"]] if isinstance(mech.get("second"), dict) else [])
    for m in items:
        if m.get("damage") is not None:
            if m.get("net_damage", 0) == 0 and not m.get("critical_injury"):
                cons.append(f"- попадание по {m.get('target')}: броня поглотила ВЕСЬ урон "
                            f"({m.get('armor_sp')} SP), цель НЕ ранена")
            else:
                cons.append(f"- попадание по {m.get('target')}: сквозь броню {m.get('net_damage')}"
                            + (", КРИТ-ТРАВМА (+5 мимо брони)" if m.get("critical_injury") else "")
                            + f", у цели HP {m.get('target_hp')} ({m.get('target_wound')})")
    r = mech.get("npc_reaction")
    if r:
        if r["success"]:
            cons.append(f"- {r['npc']} КОНТРАТАКУЕТ: урон {r['damage']} - "
                        f"SP{r.get('armor_sp', 0)} = {r['net_damage']} по игроку")
        else:
            cons.append(f"- {r['npc']} контратакует и промахивается ({r['total']} vs DV{r['dv']})")
    return "\n".join(cons) or "- урон не наносился"


@app.post("/session/{sid}/action")
def act(sid: str, req: ActionIn):
    st = SESSIONS.get(sid)
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
    rules_ctx = SEARCH.search(f"{req.text} rules", k=3)
    ctx = "\n\n---\n\n".join(f"[{m['crumb']}] {m['text'][:500]}" for m in rules_ctx)

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

    # Раскрытие сюжетного бита при успешном инфо-запросе
    info_kw = ("контракт", "детал", "цель", "информац", "чертеж", "план", "узна",
               "расскаж", "что нужно", "задан", "вопрос")
    is_info = (mech.get("action_type") in ("social", "hack", "skill")
               and not mech.get("no_roll")
               and any(k in req.text.lower() for k in info_kw))
    just_revealed = None
    if is_info and mech.get("success"):
        remaining = [b for b in CONTRACT_BEATS if b not in st["revealed_beats"]]
        if remaining:
            just_revealed = remaining[0]
            st["revealed_beats"].append(just_revealed)

    act_type = st.get("act", "fixer")
    act_ctx = {
        "fixer": (f"АКТ 1 (ТОРГ С ФИКСЕРОМ): раунд {st.get('fixer_round', 0)}, "
                  f"patience {st.get('patience', 4)}, контракт {st.get('contract', {})}"),
        "recon": (f"АКТ 2 (РЕКОГНОСЦИРОВКА): слоты {st.get('recon_slots', 0)}, "
                  f"assets {st.get('assets', [])}"),
        "infiltration": (f"АКТ 3 (ПРОНИКНОВЕНИЕ): suspicion {st.get('suspicion', 0)}, "
                         f"lockdown {st.get('lockdown', 0)}/6, assets {st.get('assets', [])}"),
    }.get(act_type, "")

    outcome = ("НЕЙТРАЛЬНО (без броска)" if mech.get("no_roll")
               else ("УСПЕХ" if mech["success"] else "ПРОВАЛ"))
    facts = json.dumps(mech, ensure_ascii=False)
    cons = consequences(mech)
    flavor = SEARCH.search(scene.split(".")[0] + " район банды техника", k=2)
    fctx = "\n".join(f"[{m['crumb']}] {m['text'][:250]}" for m in flavor)
    prev = "\n".join(f"{lg['player']}: {lg['text']} => {lg['narration'][:180]}"
                     for lg in st["log"][-2:])

    user_msg = (
        f"СЦЕНА: {scene}\n{act_ctx}\nNPC в сцене: {npc_lines}\nHeat: {st['heat']}, флаги: {st['flags']}\n"
        f"ПЕРСОНАЖ ИГРОКА: {actor['name']} ({actor['role']})\n"
        f"ЗАЯВЛЕНОЕ ДЕЙСТВИЕ: {req.text}\n"
        f"СМЫСЛ ДЕЙСТВИЯ: {ACTION_LABEL.get(mech.get('action_type'), 'действие')}\n"
        f"ФАКТЫ БРОСКА: {facts}\nРЕЗУЛЬТАТ: {outcome}\n"
        f"ПОСЛЕДСТВИЯ (обязательно соблюдать):\n{cons}\n"
        + (f"РАСКРОЙ ФАКТ СЕЙЧАС (обязательно вплести в реплику Кесслера конкретно):\n- {just_revealed}\n" if just_revealed else "")
        + (f"УЖЕ РАСКРЫТО РАНЬШЕ (не повторяй без вопроса):\n" + "\n".join("- " + b for b in st["revealed_beats"][:-1]) + "\n" if len(st["revealed_beats"]) > 1 else "")
        + (f"ФИЗИЧЕСКИ ВЫДАНО ИГРОКУ (на руках, учитывай в сценах):\n" + "\n".join("- " + g for g in st["granted"]) + "\n" if st.get("granted") else "")
        + (f"ПРЕДЫДУЩИЕ ХОДЫ:\n{prev}\n" if prev else "")
        + f"ПРАВИЛА (справочно):\n{ctx}\nЛОР (только названия и детали):\n{fctx}"
    )

    narr_sys = NARR_SYS_UNIVERSAL

    reply = chat_json([
        {"role": "system", "content": narr_sys},
        {"role": "user", "content": user_msg}
    ], model=NARR_MODEL, temperature=0.6)

    # Проверка на галлюцинации и "ты" в нарративе
    raw_n = reply.get("narration", "")
    hallucination_keywords = ["новый сент-джеймс", "клан королевских", "покровительств"]
    has_hallucination = any(kw in raw_n.lower() for kw in hallucination_keywords)
    you_patterns = [
        " ты ", "твой ", "твоя ", "твоё ", "твои ", "тебя ", "тебе ",
        " тобой", " твой ", " твоя ", " твоё ", " твои ",
        " вашего", " вашим", " ваша", " ваше"
    ]
    has_you = any(p in raw_n.lower() for p in you_patterns)

    if has_you or has_hallucination or CJK.search(raw_n) or len(clean(raw_n)) < 40:
        retry_sys = narr_sys + "\n\n**ВТОРАЯ ПОПЫТКА. ПРЕДЫДУЩИЙ ОТВЕТ НАРУШАЛ ПРАВИЛА. ПИШИ ТОЛЬКО В ТРЕТЬЕМ ЛИЦЕ.**"
        reply = chat_json([
            {"role": "system", "content": retry_sys},
            {"role": "user", "content": user_msg}
        ], model=NARR_MODEL, temperature=0.4)

    # Проверка на галлюцинации (если нарратив содержит слова, которых нет в контексте)
    raw_n = reply.get("narration", "")
    hallucination_keywords = ["новый сент-джеймс", "клан королевских", "покровительств"]
    has_hallucination = any(kw in raw_n.lower() for kw in hallucination_keywords)

    if has_hallucination or CJK.search(raw_n) or len(clean(raw_n)) < 40:
        reply = chat_json([
            {"role": "system", "content": narr_sys},
            {"role": "user", "content": user_msg}
        ], model=NARR_MODEL, temperature=0.4)

    raw_n = reply.get("narration", "")
    if CJK.search(raw_n) or len(clean(raw_n)) < 40:
        reply = chat_json([
            {"role": "system", "content": narr_sys},
            {"role": "user", "content": user_msg}
        ], model=NARR_MODEL, temperature=0.4)

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
        # Автоматический переход к Акту 2
    act_type = st.get("act", "fixer")
    if act_type == "fixer":
        # Триггер 1: игрок хочет уйти
        trigger_phrases = [req.text.lower(), (m.get("_text", "") or "").lower()]
        wants_to_leave = any(trig in phrase for phrase in trigger_phrases for trig in ACT2_TRIGGERS)
        
        # Триггер 2: Кесслер устал от провалов (только если patience = 0 ИЛИ 3+ провала)
        recent_logs = st["log"][-4:]  # последние 4 хода
        fail_count = sum(1 for lg in recent_logs if lg.get("mech", {}).get("success") is False)
        patience_low = st.get("patience", 4) <= 0
        kessler_tired = fail_count >= 3 or patience_low
        
        if wants_to_leave or kessler_tired:
            scenario.advance_act(st)
            st["act"] = "recon"
            st["recon_slots"] = 3
            st["assets"] = []
            
            if wants_to_leave:
                transition_narr = ("Вы поднимаетесь из-за стола. Кесслер кивает на прощание: "
                                   "'Удачи. Не подведите.' Он сворачивает планшет и уходит вглубь бара.\n\n"
                                   "[ПЕРЕХОД К АКТУ 2: РЕКОГНОСЦИРОВКА]\n\n"
                                   "Вы прибываете к дата-узлу Biotechnica в промзоне sector 7. "
                                   "Серое здание, камеры на углах, патрули по периметру.")
            else:
                transition_narr = ("Кесслер нетерпеливо машет рукой: 'Хватит болтать, время идёт. "
                                   "Идите и сделайте свою работу.' Он забирает планшет и уходит, "
                                   "не оглядываясь.\n\n"
                                   "[ПЕРЕХОД К АКТУ 2: РЕКОГНОСЦИРОВКА]\n\n"
                                   "Вы прибываете к дата-узлу Biotechnica в промзоне sector 7. "
                                   "Серое здание, камеры на углах, патрули по периметру.")
            
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
                "state": st
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


@app.post("/session/{sid}/turn/{tid}/rate")
def rate_turn(sid: str, tid: int, req: RateIn):
    if sid not in SESSIONS:
        raise HTTPException(404, "Session not found")
    if not (1 <= req.rating <= 5):
        raise HTTPException(400, "Rating must be 1-5")
    db.rate_turn(tid, req.rating, req.edited)
    return {"ok": True, "turn_id": tid, "rating": req.rating}