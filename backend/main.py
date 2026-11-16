# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid, json, os, re
from pathlib import Path
from contextlib import asynccontextmanager

import asyncio
import string
import random as _random
from fastapi import WebSocket, WebSocketDisconnect
from backend import inventory, body, crafting
from . import substances
from . import netrunning
from . import db, engine, scenario, chargen
from .llm import chat_json
from .rag import RulesSearch
from .common import clean, CJK
from . import spawn
from contextlib import asynccontextmanager

class ConnectionManager:
    """Хранит WebSocket-подключения по сессиям."""

    def __init__(self):
        self.conns = {}

    async def connect(self, sid, ws, player):
        await ws.accept()
        self.conns.setdefault(sid, []).append((ws, player))

    def disconnect(self, sid, ws):
        if sid in self.conns:
            self.conns[sid] = [c for c in self.conns[sid] if c[0] is not ws]

    async def broadcast(self, sid, message):
        for ws, _ in list(self.conns.get(sid, [])):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(sid, ws)


manager = ConnectionManager()
LOOP = None


@asynccontextmanager
async def lifespan(app):
    global LOOP
    LOOP = asyncio.get_running_loop()
    print("[WS] event loop сохранён")
    yield


app = FastAPI(lifespan=lifespan)


def broadcast_now(sid, message):
    if LOOP is None:
        print(f"[WARN] broadcast пропущен: LOOP is None (sid={sid})")
        return
    if not manager.conns.get(sid):
        print(f"[WARN] broadcast пропущен: нет WS-подключений (sid={sid})")
        return
    asyncio.run_coroutine_threadsafe(manager.broadcast(sid, message), LOOP)


def public_state(st):
    """Состояние без секретов (токены не отдаём клиентам)."""
    return {k: v for k, v in st.items() if k != "tokens"}


def get_state(sid):
    st = SESSIONS.get(sid)
    if st is None:
        st = db.load_session(sid)
        if st:
            SESSIONS[sid] = st
    return st


def persist(st):
    SESSIONS[st["id"]] = st
    db.save_session(st["id"], st)



def find_by_code(code):
    code = (code or "").strip().upper()
    if not code:
        return None
    for st in SESSIONS.values():
        if st.get("code") == code:
            return st
    for st in db.all_session_states():
        if st.get("code") == code:
            SESSIONS[st["id"]] = st
            return st
    return None


DEFAULT_SCENARIO = {
    "scene": ("Бар 'Ржавый болт', Ночной Город, 23:40. За угловым столом среди дыма и "
              "неоновых бликов сидит фиксер Кесслер. За барной стойкой — два его "
              "телохранителя в кевларе с тяжёлыми пистолетами под плащами. На столе у "
              "Кесслера — стакан синтетического виски и дата-планшет с контрактом."),
    "heat": 1, "clocks": {},
    "npcs": [
        {"id": "kessler", "name": "Фиксер Кесслер", "hp": 15, "max_hp": 15,
         "wound": "unharmed", "armor": "leathers"},
        {"id": "guard1", "name": "Телохранитель Кесслера 1", "hp": 24, "max_hp": 24,
         "wound": "unharmed", "armor": "kevlar"},
        {"id": "guard2", "name": "Телохранитель Кесслера 2", "hp": 24, "max_hp": 24,
         "wound": "unharmed", "armor": "kevlar"},
    ],
}

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

3. УСПЕХ/ПРОВАЛ бери из РЕЗУЛЬТАТА.
   - Если РЕЗУЛЬТАТ = УСПЕХ, но в ПОСЛЕДСТВИЯХ сказано "броня поглотила весь урон" — цель НЕ ранена, но удар пришёлся.
     Описывай: искры от брони, отдачу, контузию, цель шатается, но раны нет.
     ❌ НЕ пиши "уворачивается", "промахивается", "уходит от удара".
     ✅ ПРАВИЛЬНО: "Кулак Кулаковца бьёт в плечо охранника — kevlar глушит удар, но телохранитель шатается от силы удара."
   - Если РЕЗУЛЬТАТ = ПРОВАЛ — цель уклонилась, удар прошёл мимо.

4. ЗАПРЕЩЕНО копировать фразы из ПРИМЕРОВ и из блока ПРЕДЫДУЩИЕ ХОДЫ: каждый ход — новый кадр и новые формулировки.

5. Запрещено вводить персонажей, банды и события, которых нет в СЦЕНЕ и ФАКТАХ.

6. Числа урона, HP, DV — только из ФАКТОВ.

7. Объём 3–5 предложений, затем 1–2 вопроса и 2–4 варианта инфинитивом.

8. РЕАКЦИЯ ПЕРСОНАЖЕЙ: 
   - Если игрок УСПЕШНО атакует NPC (даже если броня поглотила урон):
     * Цель атаки ОБЯЗАНА контратаковать в том же ходу
     * ВСЕ другие враждебные NPC в сцене (охранники, телохранители) также атакуют игрока
     * Описывай КАЖДУЮ контратаку отдельно: кто стреляет, попадает/промахивается, урон
   - Если игрок ПРОВАЛИЛ атаку: цель уклонилась, но другие NPC всё равно могут атаковать
   - Пассивное поведение запрещено: NPC не могут просто "смотреть" после атаки

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
Имя может содержать латиницу и цифры (например, FRJ5UQ). Пиши его ТОЧНО как в блоке ДЕЙСТВУЕТ:
латиницей, без транслитерации в кириллицу, без сокращений и без отбрасывания символов.
❌ "5 входит", "ФРЖУКВ" — ЗАПРЕЩЕНО
✅ "FRJ5UQ входит в бар"

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
    token: Optional[str] = None


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
    
    persist(st)
    broadcast_now(sid, {"type": "state", "state": public_state(st)})    
    
    return result

@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/setup")
def setup_page():
    return FileResponse(STATIC / "setup.html")


@app.post("/chargen")
def chargen_endpoint(req: ChargenIn):
    from backend import creation
    try:
        return creation.random_character(req.role)
    except Exception as e:
        raise HTTPException(400, f"chargen: {e}")


@app.get("/creation/options")
def creation_options(role: str = None):
    from backend import creation
    return creation.options(role)


@app.post("/creation/build")
def creation_build(spec: dict):
    from backend import creation
    try:
        return creation.build(spec)
    except ValueError as e:
        raise HTTPException(400, str(e))


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
    st = get_state(sid)
    if not st:
        raise HTTPException(404)
    return public_state(st)


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


@app.post("/session/{sid}/action")
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

import re

ACT2_SCENE = ("Дата-узел Biotechnica, промзона sector 7, ночь. Серое здание без вывесок, "
              "камеры на углах, патрули охраны по периметру. У служебного входа — кодовый "
              "замок; северный забор уходит в слепую зону камер. Изнутри гудят серверные.")

ACT2_TRIGGERS_WORDS = [
    "отправляемся", "выдвигаемся", "уходим", "ухожу", "уйду", "идём", "идем",
    "едем", "пошёл", "пошла", "пошли", "погнали", "прощается", "покидает",
]
NEG_DEPARTURE = ["не ухожу", "никуда не", "остаюсь", "остаёмся", "остаемся",
                 "передумал", "передумала", "не пойду", "не идём", "не идем", "вернусь"]
CONFIRM_YES = ["да", "подтверждаю", "уходим", "идём", "идем", "пошли", "погнали", "ухожу"]
CONFIRM_NO = ["нет", "остаюсь", "остаёмся", "остаемся", "передумал", "передумала", "вернусь"]


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

LOCATION_RU = {"head": "голова", "torso": "корпус", "limb": "конечность", "auto": "корпус"}

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

_FLAVOR_FORBID = ("попал", "попадает", "промах", "урон", "поглот", "брон", "ранен",
                  "убит", "умер", "sp", "кевлар", "луч", "лазер", "плазм")


def _clean_flavor(s, default, block=()):
    s = (s or "").strip()
    low = s.lower()
    if not s or any(t in low for t in _FLAVOR_FORBID):
        return default
    if any(b and b.lower() in low for b in block):
        return default
    return s


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


ACCEPT_WORDS = ("беру", "согласен", "согласна", "принимаю", "подписываю", "по рукам", "deal")


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


ACCEPT_WORDS = ("беру", "согласен", "согласна", "принимаю", "подписываю", "по рукам", "deal")


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


ACCEPT_WORDS = ("беру", "согласен", "согласна", "принимаю", "подписываю", "по рукам", "deal")


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

class CreateLobby(BaseModel):
    player_name: str
    character: dict


class JoinLobby(BaseModel):
    code: str
    player_name: str
    character: dict


@app.post("/lobby/create")
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


@app.post("/lobby/join")
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


@app.post("/lobby/{sid}/start")
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
 
@app.websocket("/ws/{sid}")
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

@app.get("/data/substances")
def data_substances():
    from backend import substances
    return {"drugs": list(substances.DRUGS.keys()),
            "poisons": list(substances.POISONS.keys())}


@app.get("/data/recipes")
def data_recipes():
    from backend import crafting
    out = {}
    for k, v in crafting.RECIPES.items():
        out[k] = {"name": v["name"], "components": v["components"],
                  "skill": v["skill"], "dv": v["dv"]}
    return {"recipes": out}        
    