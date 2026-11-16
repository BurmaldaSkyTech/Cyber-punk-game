РОЛЬ: экстрактор правил. Источник — приложенный PDF Cyberpunk RED Core Rulebook.
Схема вывода та же, что в REVIEW_BUNDLE.json (entries / not_found / code_discrepancies).
Требования прежние: только JSON, page обязателен, quote ≤200 символов содержит значение,
ничего не додумывать — при отсутствии писать в not_found.

ЗАДАЧА 1 — разрешить противоречие первого прохода:
creation.stat_pool_edgerunner. В прошлый раз пришло ДВА разных утверждения:
(a) строка "template roll (no fixed pool; Complete Package uses 62)" со стр.78,
(b) число 62 со стр.79 ("Starting Character 62").
Найди раздел создания персонажа и выпиши ОТДЕЛЬНО, для КАЖДОГО метода
(Streetrat / Edgerunner / Complete Package): сколько очков STAT и сколько очков Skill,
и есть ли пул вообще. Ключи: stat_pool_streetrat, stat_pool_edgerunner,
stat_pool_complete_package, skill_pool_streetrat, skill_pool_edgerunner,
skill_pool_complete_package. Значения — числа или null, без прозы.

ЗАДАЧА 2 — проверить цитату: skill_max_at_creation=6 была обоснована фразой
"No Skill can be higher than 6 or lower than 2". Уточни, относится ли она к Skills
или к STATs, и приведи точную фразу про лимит навыков при создании.

ЗАДАЧА 3 — исправить сопоставления: grenade (ручная граната) НЕ равен Grenade Launcher;
bodyplate НЕ приравнивать к Metalgear без прямого текста. Дай отдельные записи
для hand grenade и grenade launcher со своими страницами.

ЗАДАЧА 4 — извлечь недостающее, ища по заголовкам разделов:
combat.range_dv — таблица DV по дистанциям для каждого типа оружия
combat.aimed_shot_penalties — штрафы за прицельный выстрел (голова/конечность)
combat.aimed_shot_multipliers — множители урона при попадании в голову/конечность
combat.armor_ablation — правило износа брони (на сколько падает SP и при каком условии)
combat.critical_injury_trigger — сколько шестёрок на кубиках урона дают крит
combat.critical_injury_bonus — размер бонусного урона при крите
combat.critical_injury_table — таблица критических травм (ключ: бросок/диапазон)
combat.wound_states — пороги HP для состояний ранения
combat.wound_penalties — штрафы за состояния ранения
combat.death_save_formula — точное правило Death Save
combat.initiative_formula — правило инициативы
combat.autofire_rules — режим автоогня (навык, DV, множитель)
combat.rof_rules — что означает ROF и сколько выстрелов за действие
combat.melee_opposed_by / combat.ranged_defense — чем защищается цель
creation.skill_list — полный список навыков с привязкой к STAT (объект {key: stat})
creation.stat_list — список STAT
creation.roles — список ролей
netrunning.architectures / program_list / interface_dv / black_ice
cyberware.table / humanity_loss_rules
gear.table / services

Большие таблицы можно разбивать на несколько записей с суффиксами
(critical_injury_table_head, critical_injury_table_torso, ...), но каждая
обязана иметь свою страницу и цитату.