# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid, json, os, re
from pathlib import Path

from backend import inventory, body, crafting
from . import substances
from . import netrunning
from . import db, engine, scenario, chargen
from .llm import chat_json
from .rag import RulesSearch
from .common import clean, CJK
from . import spawn


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
   - Если игрок использует приём боевого искусства (удар ногой, блок, подсечка, бросок, разоружение, удушение) — добавь поле "move": "название_приёма" (например, "high_kick", "sweep", "throw").
   - Список доступных приёмов зависит от стиля персонажа (martial_arts навык 2+).
2. ВЗЛОМ: сеть, электроника, замки, камеры → hack или skill.
2.5 ТРАНСПОРТ: вождение, манёвр, погоня, таран, посадка в машину → drive / ram.
   - "садится в машину", "газует", "маневрирует", "уходит от погони" → drive
   - "таранит", "врезается в машину" → ram
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
"делаю подсечку" -> {"action_type":"attack_melee","skill":"martial_arts","dv_key":"difficult","weapon":null,"move":"sweep","target":"guard1","second":null,"query":"martial arts sweep"}
"бросаю противника через бедро" -> {"action_type":"attack_melee","skill":"martial_arts","dv_key":"professional","weapon":null,"move":"throw","target":"guard1","second":null,"query":"martial arts throw"}
"газует и уходит от погони" -> {"action_type":"drive","skill":"drive_land_vehicle","dv_key":"difficult","weapon":null,"target":null,"second":null,"query":"drive chase maneuver"}
"таранит машину охранника" -> {"action_type":"ram","skill":"drive_land_vehicle","dv_key":"professional","weapon":null,"target":"guard1","second":null,"query":"ram vehicle damage"}

dv_key: тривиально -> everyday; настороже -> difficult; защита -> professional; на грани -> heroic.
skill строго из списка персонажа.
Верни ТОЛЬКО JSON."""

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

1. **СТРОГО ТРЕТЬЕ ЛИЦО.** Используй только имя персонажа игрока или "он"/"она"/"они". **КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНЫ** обращения "ты", "твой", "тебя", "тебе", "ваш", "ваше" в описаниях.
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

=== ТРЕБОВАНИЯ К КАЧЕСТВУ ===

1. Минимум 3 предложения описания + минимум 1 прямая реплика персонажа (если в сцене есть собеседник).
2. Реплики должны быть живыми: с деталями, интонацией, специфичными словами.
3. Грамматика: соблюдай род и число.
4. Если игрок здоровается или задаёт вопрос персонажу — персонаж ОБЯЗАН ответить репликой.
5. Каждый ход должен двигать сюжет: раскрывать факт, менять состояние, создавать выбор.

=== ИМЕНА ПЕРСОНАЖЕЙ ===

Используй ТОЛЬКО имена из блоков ДЕЙСТВУЕТ и NPC В СЦЕНЕ.
ЗАПРЕЩЕНО придумывать или подставлять любые другие имена (Вектор, Никс и т.п.).
Если имя персонажа — число или нестандартное слово, используй его БЕЗ склонения.

Верни только JSON:
{"narration": str, "questions": [str], "choices": [str],
 "safe_state_suggestions": {"heat_delta": -1|0|1, "add_flags": [str],
  "grant_items": [str из списка: assault_rifle, smg, cam_jammer, fake_pass, medkit, grapnel],
  "npc_action": str}}"""


# Хелпер для проверки утечек имён
EXAMPLE_NAMES = ["вектор", "никс"]


def leaked_example_names(text, st):
    """Возвращает имена-примеры, которых нет среди реальных персонажей сцены."""
    low = text.lower()
    allowed = ([p["name"].lower() for p in st["players"]] +
               [n["name"].lower() for n in st.get("npcs", [])])
    return [n for n in EXAMPLE_NAMES if n in low and n not in allowed]


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

class UseIn(BaseModel):
    item: str


@app.post("/session/{sid}/player/{player}/use")
def use_item_endpoint(sid: str, player: str, req: UseIn):
    from backend import substances, inventory
    st = SESSIONS.get(sid)
    if not st:
        raise HTTPException(404)
    actor = next((p for p in st["players"] if p["name"] == player), None)
    if not actor:
        raise HTTPException(404, "no such player")
    
    # Проверяем, есть ли предмет в инвентаре
    if not inventory.has_item(actor, req.item):
        raise HTTPException(400, "Предмета нет в инвентаре")
    
    # Применяем вещество
    result = substances.apply_substance(actor, req.item)
    if not result["success"]:
        raise HTTPException(400, result["reason"])
    
    # Убираем предмет из инвентаря
    inventory.remove_item(actor, req.item)
    
    return result

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
    """Валидирует персонажа из ручного ввода."""
    try:
        ch = chargen.manual_character(req)
    except KeyError as e:
        return {"valid": False, "problems": [f"Отсутствует поле: {e}"]}
    except Exception as e:
        return {"valid": False, "problems": [f"Ошибка: {str(e)}"]}
    
    problems = []
    stats = ch.get("stats", {})
    stat_sum = sum(stats.values())
    if stat_sum != 62:
        problems.append(f"Сумма статов должна быть 62, получено {stat_sum}")
    
    for s in ["INT", "REF", "DEX", "TECH", "COOL", "WILL", "LUCK", "MOVE", "BODY", "EMP"]:
        v = stats.get(s, 0)
        if v < 2 or v > 8:
            problems.append(f"Стат {s} должен быть 2-8, получено {v}")
    
    expected_hp = stats.get("BODY", 5) * 2
    if ch.get("hp") != expected_hp or ch.get("max_hp") != expected_hp:
        problems.append(f"HP должно быть {expected_hp}")
    
    if not ch.get("name"):
        problems.append("Имя обязательно")
    if not ch.get("role"):
        problems.append("Роль обязательна")
    
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
    result = _act_core(sid, req)
    if result is None:
        st = SESSIONS.get(sid)
        print(f"[ERROR] act() вернула None: sid={sid}, player={req.player}, text={req.text!r}")
        result = {
            "mechanics": {"action_type": "free", "no_roll": True},
            "narration": "(Внутренняя ошибка: ветка act() без возврата. Действие учтено как свободное.)",
            "questions": [],
            "choices": [],
            "turn_no": (len(st["log"]) - 1) if st else 0,
            "turn_id": None,
            "next_player": st["order"][st["turn"]] if st else "",
            "state": st,
        }
    return result


def _act_core(sid: str, req: ActionIn):
    st = SESSIONS.get(sid)
    print(f"[DEBUG act] st found: {st is not None}")
    if not st:
        raise HTTPException(404)

    actor = next((p for p in st["players"] if p["name"] == req.player), None)
    print(f"[DEBUG act] actor found: {actor is not None}, req.player={req.player!r}")
    print(f"[DEBUG act] players names: {[p['name'] for p in st['players']]}")
    if not actor:
        raise HTTPException(404, "no such player")

    expected = st["order"][st["turn"]]
    print(f"[DEBUG act] expected={expected!r}, turn={st['turn']}")
    if req.player != expected:
        raise HTTPException(409, f"Сейчас ходит {expected}, а не {req.player}")

    scene = st["scenario"].get("scene", "")
    print(f"[DEBUG act] scene ok")
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

    actor_name = actor["name"]
    players_names = ", ".join(p["name"] for p in st["players"])
    npc_block = spawn.npc_context(st)
 
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
        {"role": "system", "content": narr_sys},
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
    if act_type == "fixer":
        trigger_phrases = [req.text.lower(), (mech.get("_text", "") or "").lower()]
        wants_to_leave = any(trig in phrase for phrase in trigger_phrases for trig in ACT2_TRIGGERS)
        
        recent_logs = st["log"][-4:]
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


class BuyIn(BaseModel):
    item: str
    qty: int = 1


class InstallIn(BaseModel):
    ware: str


@app.post("/session/{sid}/player/{player}/buy")
def buy_item_endpoint(sid: str, player: str, req: BuyIn):
    from backend import inventory
    st = SESSIONS.get(sid)
    if not st:
        raise HTTPException(404)
    actor = next((p for p in st["players"] if p["name"] == player), None)
    if not actor:
        raise HTTPException(404, "no such player")
    result = inventory.buy_item(actor, req.item, qty=req.qty)
    if not result["success"]:
        raise HTTPException(400, result["reason"])
    return result


@app.post("/session/{sid}/player/{player}/install")
def install_cyberware_endpoint(sid: str, player: str, req: InstallIn):
    from backend import body
    st = SESSIONS.get(sid)
    if not st:
        raise HTTPException(404)
    actor = next((p for p in st["players"] if p["name"] == player), None)
    if not actor:
        raise HTTPException(404, "no such player")
    result = body.install_cyberware(actor, req.ware, pay_eb=True)
    if not result["success"]:
        raise HTTPException(400, result["reason"])
    return result


@app.get("/session/{sid}/player/{player}/inventory")
def get_inventory(sid: str, player: str):
    st = SESSIONS.get(sid)
    if not st:
        raise HTTPException(404)
    actor = next((p for p in st["players"] if p["name"] == player), None)
    if not actor:
        raise HTTPException(404, "no such player")
    from backend import inventory, body
    return {
        "player": player,
        "eb": actor.get("eb", 0),
        "inventory": actor.get("inventory", []),
        "capacity": inventory.capacity(actor),
        "used_slots": inventory.used_slots(actor),
        "cyberware": actor.get("cyberware", []),
        "humanity": actor.get("humanity", 0),
    }


@app.get("/shop/catalog")
def shop_catalog():
    """Возвращает каталог магазина: оружие, броня, импланты, снаряжение, транспорт."""
    from backend import inventory, body, crafting, vehicles as vehicles_mod
    catalog = []
    for key, data in inventory.WEAPONS.items():
        catalog.append({
            "key": key, "name": data.get("name", key),
            "category": "weapon", "price": data.get("price", 0),
        })
    for key, data in inventory.ARMOR.items():
        catalog.append({
            "key": key, "name": data.get("name", key),
            "category": "armor", "price": data.get("price", 0),
        })
    for key, data in body.CYBERWARE.items():
        catalog.append({
            "key": key, "name": data.get("name", key),
            "category": "cyberware", "price": data.get("price", 0),
            "slot": data.get("slot", "none"),
        })
    for key, data in inventory.GEAR.items():
        catalog.append({
            "key": key, "name": data.get("name", key),
            "category": "gear", "price": data.get("price", 0),
        })
    for key, data in inventory.COMPONENTS.items():
        catalog.append({
            "key": key, "name": data.get("name", key),
            "category": "component", "price": data.get("price", 0),
        })
    for key, data in vehicles_mod.VEHICLES.items():
        catalog.append({
            "key": key, "name": data.get("name", key),
            "category": "vehicle", "price": data.get("price", 0),
        })
    return catalog
 

class CraftIn(BaseModel):
    recipe: str


class RepairIn(BaseModel):
    item: str


@app.post("/session/{sid}/player/{player}/craft")
def craft_endpoint(sid: str, player: str, req: CraftIn):
    from backend import crafting
    st = SESSIONS.get(sid)
    if not st:
        raise HTTPException(404)
    actor = next((p for p in st["players"] if p["name"] == player), None)
    if not actor:
        raise HTTPException(404, "no such player")

    recipe = crafting.get_recipe(req.recipe)
    if not recipe:
        raise HTTPException(400, "Неизвестный рецепт")

    skill_key = recipe["skill"]
    stat = actor["stats"].get("TECH", 2)
    skill = actor["skills"].get(skill_key, 0)
    mech = engine.skill_check(stat, skill, recipe["dv"])

    result = crafting.attempt_craft(actor, req.recipe, mech["total"])
    return {"mechanics": mech, "recipe": req.recipe, **result}


@app.post("/session/{sid}/player/{player}/repair")
def repair_endpoint(sid: str, player: str, req: RepairIn):
    from backend import crafting
    st = SESSIONS.get(sid)
    if not st:
        raise HTTPException(404)
    actor = next((p for p in st["players"] if p["name"] == player), None)
    if not actor:
        raise HTTPException(404, "no such player")

    mech = engine.skill_check(actor["stats"].get("TECH", 2),
                              actor["skills"].get("basic_tech", 0), 13)
    result = crafting.repair_item(actor, req.item, mech["total"])
    return {"mechanics": mech, **result} 
    
class VehicleIn(BaseModel):
    vehicle: str


@app.post("/session/{sid}/player/{player}/vehicle/board")
def vehicle_board(sid: str, player: str, req: VehicleIn):
    from backend import vehicles
    st = SESSIONS.get(sid)
    if not st:
        raise HTTPException(404)
    actor = next((p for p in st["players"] if p["name"] == player), None)
    if not actor:
        raise HTTPException(404, "no such player")
    result = vehicles.board_vehicle(actor, req.vehicle)
    if not result["success"]:
        raise HTTPException(400, result["reason"])
    return result


@app.post("/session/{sid}/player/{player}/vehicle/exit")
def vehicle_exit(sid: str, player: str):
    from backend import vehicles
    st = SESSIONS.get(sid)
    if not st:
        raise HTTPException(404)
    actor = next((p for p in st["players"] if p["name"] == player), None)
    if not actor:
        raise HTTPException(404, "no such player")
    result = vehicles.exit_vehicle(actor)
    if not result["success"]:
        raise HTTPException(400, result["reason"])
    return result


@app.post("/session/{sid}/player/{player}/vehicle/buy")
def vehicle_buy(sid: str, player: str, req: VehicleIn):
    from backend import vehicles
    st = SESSIONS.get(sid)
    if not st:
        raise HTTPException(404)
    actor = next((p for p in st["players"] if p["name"] == player), None)
    if not actor:
        raise HTTPException(404, "no such player")
    result = vehicles.buy_vehicle(actor, req.vehicle)
    if not result["success"]:
        raise HTTPException(400, result["reason"])
    return result