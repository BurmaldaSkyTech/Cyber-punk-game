# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid, json, os
from pathlib import Path

from . import db, engine
from .llm import chat_json
from .rag import RulesSearch
from .common import clean, CJK

app = FastAPI()

# CORS для веб-клиента (доступ с любых адресов)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы для веб-клиента
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
}

JUDGE_SYS = """Ты — механический интерпретатор правил Cyberpunk RED. Никакой прозы, только JSON:
{"action_type": "skill|attack_ranged|attack_melee|hack|social|heal",
 "skill": "ключ навыка строго из списка персонажа",
 "dv_key": "simple|everyday|difficult|professional|heroic|incredible|legendary",
 "weapon": "ключ оружия или null", "target": "id NPC или null",
 "second": null или такой же объект для ВТОРОЙ части составного действия,
 "query": "короткий запрос для поиска правил"}

ПРИМЕРЫ:
"стреляю в охранника из тяжёлого пистолета" -> {"action_type":"attack_ranged","skill":"handgun","dv_key":"difficult","weapon":"heavy_pistol","target":"guard1","second":null,"query":"ranged attack DV"}
"этот пьяный придурок в меня врезался и пытается выставить виноватым" (словами отводит вину) -> {"action_type":"social","skill":"persuasion","dv_key":"everyday","weapon":null,"target":"guard1","second":null,"query":"social opposed check"}
"кинул гранату, затем взломал его канал связи" -> {"action_type":"attack_ranged","skill":"athletics","dv_key":"difficult","weapon":"grenade","target":"guard1","second":{"action_type":"hack","skill":"interface","dv_key":"professional","weapon":null,"target":null},"query":"grenade damage"}
"пройти мимо курьера и незаметно дёрнуть флешку" -> {"action_type":"skill","skill":"stealth","dv_key":"difficult","weapon":null,"target":"courier","second":null,"query":"pickpocket stealth DV"}
"нетран, взлом сети, подключение к системе, создать помехи в электронике" -> {"action_type":"hack","skill":"interface","dv_key":"professional","weapon":null,"target":null,"query":"netrunning hack DV"}

ГЛАВНОЕ: если персонаж ГОВОРИТ, лжёт, притворяется — это social, НЕ атака. Атака — только насилие или выстрел. Граната/бомба -> attack_ranged, weapon grenade.
Ключевые слова "нетран", "взлом сети", "подключение к системе", "создать помехи в электронике" ВСЕГДА -> hack, НЕ social.
Составное действие ("затем", "сразу после", "и тут же") -> первая часть в основные поля, вторая в second.
Местоимения ("него", "ему") относят к ТЕКУЩЕЙ УГРОЗЕ, если она указана.
skill строго из списка персонажа. dv_key: в упор/тривиально -> everyday; цель настороже, средняя дистанция -> difficult; взлом защиты, дальний бой -> professional; на грани -> heroic.
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
9. РЕАКЦИЯ NPC: Если игрок успешно атакует или взламывает NPC, NPC должен активно реагировать: отбиваться, уклоняться, контратаковать, звать подмогу, хватать оружие. Пассивное поведение ("он просто стоит") запрещено.

ПРИМЕРЫ (копировать их фразы запрещено):
ФАКТЫ: действие "незаметно дёрнуть флешку", ПРОВАЛ, margin -2
НАРРАТИВ: "Локоть курьера в последний момент уходит в сторону — пальцы смыкаются на пустой ткани. Он резко оборачивается, прижимая флешку к груди, и его глаза мечутся в поисках охраны."
ФАКТЫ: действие "выстрелить в охранника", УСПЕХ, net_damage 0, armor_sp 7
НАРРАТИВ: "Пуля заставляет охранника дёрнуться, но тяжёлый armorjack лишь щёлкает под ударом: пластина держит. Он ныряет за прилавок и хрипло кричит что-то в рацию."

Верни только JSON:
{"narration": str, "questions": [str], "choices": [str],
 "safe_state_suggestions": {"heat_delta": -1|0|1, "add_flags": [str], "clock_progress": {name: 0|1|2}, "npc_action": str}}"""


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


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.post("/session")
def new_session(req: NewSession):
    sid = uuid.uuid4().hex[:8]
    SESSIONS[sid] = {
        "id": sid, "scenario": req.scenario,
        "heat": req.scenario.get("heat", 0),
        "clocks": req.scenario.get("clocks", {}),
        "flags": [], "log": [], "turn": 0, "threat": None,
        "order": [p["name"] for p in req.players],
        "players": req.players, "npcs": req.scenario.get("npcs", [])}
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
    return {"heat_delta": hd, "add_flags": flags, "clock_progress": clocks, "npc_action": npc_action}


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

    # NPC контратакует один раз после действия игрока (при активном бое)
    reaction = engine.resolve_npc_reaction(st, actor, mech)
    if reaction:
        mech["npc_reaction"] = reaction

    for m in [mech] + ([mech["second"]] if isinstance(mech.get("second"), dict) else []):
        if m.get("target_id"):
            st["threat"] = m["target_id"]

    outcome = "УСПЕХ" if mech["success"] else "ПРОВАЛ"
    facts = json.dumps(mech, ensure_ascii=False)
    cons = consequences(mech)
    flavor = SEARCH.search(scene.split(".")[0] + " район банды техника", k=2)
    fctx = "\n".join(f"[{m['crumb']}] {m['text'][:250]}" for m in flavor)
    prev = "\n".join(f"{lg['player']}: {lg['text']} => {lg['narration'][:180]}"
                     for lg in st["log"][-2:])

    user_msg = (
        f"СЦЕНА: {scene}\nNPC в сцене: {npc_lines}\nHeat: {st['heat']}, флаги: {st['flags']}\n"
        f"ПЕРСОНАЖ ИГРОКА: {actor['name']} ({actor['role']})\n"
        f"ЗАЯВЛЕНОЕ ДЕЙСТВИЕ: {req.text}\n"
        f"СМЫСЛ ДЕЙСТВИЯ: {ACTION_LABEL.get(mech.get('action_type'), 'действие')}\n"
        f"ФАКТЫ БРОСКА: {facts}\nРЕЗУЛЬТАТ: {outcome}\n"
        f"ПОСЛЕДСТВИЯ (обязательно соблюдать):\n{cons}\n"
        + (f"ПРЕДЫДУЩИЕ ХОДЫ:\n{prev}\n" if prev else "")
        + f"ПРАВИЛА (справочно):\n{ctx}\nЛОР (только названия и детали):\n{fctx}")

    reply = chat_json([
        {"role": "system", "content": NARR_SYS},
        {"role": "user", "content": user_msg}
    ], model=NARR_MODEL, temperature=0.6)

    raw_n = reply.get("narration", "")
    if CJK.search(raw_n) or len(clean(raw_n)) < 40:
        reply = chat_json([
            {"role": "system", "content": NARR_SYS},
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