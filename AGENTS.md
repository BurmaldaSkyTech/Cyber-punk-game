# Соглашения проекта (обязательны к чтению перед любой правкой)

## Инварианты архитектуры
1. backend/engine.py — ЕДИНСТВЕННЫЙ источник правил: кубы, урон, SP, DV, раны,
   death save. LLM не вычисляет числа никогда.
2. Любой ответ LLM проходит backend/llm.chat_json и валидацию/клампы в main.py.
   Сырой текст модели не попадает в состояние сессии.
3. Числа (DV, урон, SP, цены) читаются из PostgreSQL game_data
   (семейства dv_table, weapons, armor, ...), фолбэк data/rules/*.json.
4. Проза и лор — только из RAG (index/embeddings.npy + meta.jsonl, lore_chunks).
5. data/extracted, data/tables, data/chunks, data/normalized, index/ —
   ГЕНЕРИРУЕМЫЕ артефакты: руками не править, в рефакторинг не включать.
6. validate() и очередь ревью неприкасаемы: это защита от галлюцинаций.

## Стиль
- Python 3.12, новые зависимости только с обоснованием в коммите.
- JSON-контракты judge/narrator/engine зафиксированы в backend/main.py.
- После КАЖДОЙ правки: python -m pytest -q зелёный.

## Запрещено без явной задачи
- Менять тексты JUDGE_SYS / NARR_SYS и few-shot примеры.
- Менять эвристики scripts/01_extract.py (колонки, дроп-кэпы, колонтитулы).
- Убирать фолбэки БД->JSON.

## Бэклог чистки
T1. Вынести slug(), flat(), flat_cells(), validate(), clean() в backend/common.py,
    убрать дубли из 11_*, 14_*, main.py.
T2. Пакет cpr/ с CLI: python -m cpr extract|chunk|index|tables|normalize|review|load|search|play.
T3. Единый репозиторий-слой cpr/repo.py: всё чтение game_data/lore/sessions/turns только через него.
T4. Единый Ollama-клиент cpr/llm.py: chat_json + embed + фолбэк /api/generate.
T5. Конфиг cpr/config.py (пути, модели, DSN) вместо разбросанных констант.
T6. pyproject.toml + requirements.txt + README.md с quickstart.
T7. Убрать сгенерированное из git (уже в .gitignore).
T8. Расширить tests/: спецы unwrap для armor/weapons/wound_states, фолбэк БД->JSON.