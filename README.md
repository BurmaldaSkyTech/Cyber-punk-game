\# Cyberpunk RED - AI Game Master



Текстовая настольная ролевая игра Cyberpunk RED с AI-гейм-мастером на основе локальных LLM.



\## Особенности



\- \*\*Локальные LLM\*\*: Работает полностью оффлайн на Ollama (Qwen2.5 7B + 14B)

\- \*\*RAG по книге правил\*\*: Поиск в corebook Cyberpunk RED (1226 чанков, BM25 + эмбеддинги)

\- \*\*Детерминированная механика\*\*: Все броски кубов, урон, SP, DV вычисляются кодом, не LLM

\- \*\*PostgreSQL интеграция\*\*: Все данные (оружие, броня, навыки) в БД с JSON-фолбэком

\- \*\*Веб-клиент\*\*: Браузерный интерфейс для мультиплеера через Radmin VPN

\- \*\*Детерминированная нормализация\*\*: 17 типов оружия и 9 типов брони извлечены из свёрнутых PDF-таблиц

\- \*\*Система рейтинга\*\*: Оценка нарратива для дообучки модели (QLoRA)



\## Архитектура

┌─────────────┐ ┌──────────────┐ ┌─────────────┐
│ Веб-клиент │────▶│ FastAPI │────▶│ PostgreSQL │
│ (HTML/JS) │ │ backend/ │ │ (game_data)│
└─────────────┘ └──────────────┘ └─────────────┘
│
├─▶ Ollama (Qwen2.5 7B - Judge)
├─▶ Ollama (Qwen2.5 14B - Narrator)
├─▶ Ollama (BGE-M3 - Embeddings)
└─▶ RAG (1226 chunks)


### Компоненты

- **backend/engine.py** — Механика игры: броски кубов, урон, SP, раны, death save
- **backend/llm.py** — Обёртка над Ollama API с fallback на /api/generate
- **backend/rag.py** — Гибридный поиск: BM25 + косинусное сходство эмбеддингов
- **backend/db.py** — PostgreSQL клиент с кэшированием соединений
- **backend/main.py** — FastAPI сервер, промпты Judge/Narrator, логика ходов
- **backend/common.py** — Утилиты: slug, validate, clean (CJK/latin)
- **scripts/** — Пайплайн обработки PDF (извлечение → чанки → индекс → нормализация)

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt

2. Установка моделей

ollama pull qwen2.5:7b-instruct
ollama pull qwen2.5:14b
ollama pull bge-m3

3. Настройка PostgreSQL

psql -U postgres -p 7777 -c "CREATE DATABASE cpr;"
psql -U postgres -p 7777 -d cpr -f schema.sql

4.Обработка книги правил

# Извлечение текста и таблиц из PDF
python scripts/01_extract.py

# Создание чанков для RAG
python scripts/02_chunk.py

# Фикс можибаки и создание индекса
python scripts/09_fix_mojibake.py
python scripts/03_index.py

# Нормализация таблиц
python scripts/11_normalize_tables.py

# Загрузка в PostgreSQL
python scripts/12_pg_load.py

5. Запуск сервера

uvicorn backend.main:app --host 0.0.0.0 --port 8000

6. Мультиплеер через Radmin VPN

Установи Radmin VPN
Создай сеть (например, CyberpunkGame)
Выдать другому пользователю свой виртуальный IP
Второй пользователь открывает http://ТВОЙ_IP:8000 в браузере

Структура проекта

cyberpunk-red-game/
├── backend/                 # Серверная логика
│   ├── main.py             # FastAPI endpoints
│   ├── engine.py           # Игровая механика
│   ├── llm.py              # Ollama клиент
│   ├── rag.py              # Поиск по правилам
│   ├── db.py               # PostgreSQL
│   └── common.py           # Утилиты
├── scripts/                # Пайплайн обработки PDF
│   ├── 01_extract.py       # Извлечение из PDF
│   ├── 02_chunk.py         # Чанкинг
│   ├── 03_index.py         # Индексация эмбеддингов
│   ├── 09_fix_mojibake.py  # Фикс кодировки
│   ├── 11_normalize_tables.py  # Нормализация таблиц
│   └── 12_pg_load.py       # Загрузка в PostgreSQL
├── data/
│   ├── raw/                # Исходный PDF
│   ├── extracted/          # Извлечённые блоки/таблицы
│   ├── chunks/             # Чанки для RAG
│   ├── normalized/         # Нормализованные таблицы
│   └── rules/              # JSON-фолбэк (weapons/armor/dv)
├── index/                  # Эмбеддинги + метаданные
├── static/                 # Веб-клиент (HTML/JS/CSS)
├── tests/                  # Pytest тесты
├── schema.sql              # PostgreSQL схема
└── requirements.txt


Технические детали
Детерминированная нормализация
Книга содержит свёрнутые таблицы (например, броня на стр. 351): сначала названия в три колонки, потом "Damage Stopping Power (SP)" как заголовок внутри ячейки, потом числа SP.
Решение: scripts/16_fix_armor_weapons.py — детерминированный парсер, который извлекает:
17 типов оружия (Medium Pistol, Heavy Pistol, SMG, Assault Rifle, Sniper Rifle, и т.д.)
9 типов брони (Leathers SP=4, Kevlar SP=7, Light Armorjack SP=11, ..., Metalgear SP=18)
Промпт-инжиниринг
Judge (Qwen2.5 7B):
Классифицирует действия игрока: attack_ranged, attack_melee, hack, social, skill
Выбирает DV из 7 уровней сложности
Определяет оружие и цель
Поддерживает составные действия (second action)
Narrator (Qwen2.5 14B):
Генерирует 3–5 предложений нарратива
Соблюдает последствия броска (успех/провал, урон/броня)
Правило 9: NPC активно реагирует (контратакует, уклоняется, зовёт подмогу)
clean() убирает CJK-иероглифы и латинские осколки

Механика игры

# backend/engine.py
def resolve_check(state, actor, judge):
    dv = DV.get(judge["dv_key"], 13)
    stat = actor["stats"][SKILL_STAT[judge["skill"]]]
    skill = actor["skills"][judge["skill"]]
    mods = WOUND_MOD[actor["wound"]]
    
    mech = skill_check(stat, skill, dv, mods)
    
    if mech["success"] and judge["action_type"] in ("attack_ranged", "attack_melee"):
        weapon = WEAPONS[judge["weapon"]]
        damage = roll_dice(weapon["damage"])
        armor_sp = ARMOR[target["armor"]]["sp"]
        net_damage = max(0, damage - armor_sp)
        apply_damage(target, net_damage)
    
    return mech
	
RAG (Retrieval-Augmented Generation)

# backend/rag.py
class RulesSearch:
    def search(self, query, k=4):
        qv = self.embed(query)  # BGE-M3 embedding
        sims = self.emb @ qv    # косинусное сходство
        vec_order = np.argsort(-sims)[:k*6]
        bm_order = self.bm25.get_scores(tokenize(query))[:k*6]
        # Reciprocal Rank Fusion
        scores = {idx: 1/(60+rank) for rank, idx in enumerate(vec_order)}
        for rank, idx in enumerate(bm_order):
            scores[idx] += 1/(60+rank)
        return sorted(scores, key=lambda x: -x[1])[:k]

Тестирование

python -m pytest -q
# 11 passed (roll_d10, roll_dice, wound_state, resolve_attack, validate, clean)

1. Накопление датасета
Играй сессии, оценивай нарратив через веб-интерфейс (звёзды 1–5). Ходы с rating >= 4 или edited_narration попадают в датасет.

python scripts/15_export_dataset.py
# Экспорт ~200-500 пар (факты → эталонный нарратив)

2. Обучение

# Используй Unsloth для QLoRA на RTX 5070
# Датасет: data/dataset/dataset.jsonl
# Базовая модель: qwen2.5:7b
# Время: 2-4 часа

3. Экспорт

# GGUF → Ollama
ollama create narrator-finetuned -f Modelfile

Производительность
Извлечение PDF: 3–10 мин (458 страниц, 26083 блоков, 223 таблицы)
Чанкинг: <1 сек (1226 чанков)
Индексация: 4 мин (BGE-M3 эмбеддинги)
Нормализация: 10–15 мин (1147 строк game_data)
Запуск сервера: 10 сек (загрузка RAG индекса)
Ход игры: 5–15 сек (Judge + Narrator)
Системные требования
RAM: 16 GB (рекомендуется 32 GB для Qwen2.5 14B)
VRAM: 12 GB (Qwen2.5 7B) или 24 GB (Qwen2.5 14B)
Диск: 50 GB (модели + данные)
CPU: Любой современный (BGE-M3 эмбеддинги на CPU)
Лицензия
MIT
Контакты
Автор: Лев
GitHub: 
Email: ldonskov23@mail.ru
Roadmap
Визуальный интерфейс (Streamlit/Gradio)
Карта Найт-Сити с токенами персонажей
Сохранение/загрузка сессий
Мультиплеер с авторизацией
Дообучение нарратора на оценённых ходах
Экспорт в PDF (красивый лог сессии)
Благодарности
R. Talsorian Games за Cyberpunk RED
Ollama за локальный inference
Qwen Team за Qwen2.5 модели
BGE Team за эмбеддинги