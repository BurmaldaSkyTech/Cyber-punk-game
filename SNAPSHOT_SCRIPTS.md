# Scripts snapshot: Scripts


===== Scripts\01_extract.py (232 строк) =====

--- поверхность модуля ---
PDF_PATH, OUT_DIR, find_boilerplate, is_boiler, inside_any_bbox, cells_from_words, drop_empty_cols, rows_to_markdown, page_columns, merge_dropcaps, main


===== Scripts\02_chunk.py (122 строк) =====

--- поверхность модуля ---
IN_DIR, OUT, MAX_CHARS, MIN_CHARS, load_toc, is_heading, PathStack, main


===== Scripts\03_index.py (59 строк) =====

--- поверхность модуля ---
OLLAMA_EMBED, OLLAMA_EMBED_LEGACY, MODEL, BATCH, CHUNKS, INDEX_DIR, embed_batch, main


===== Scripts\04_tables.py (31 строк) =====

--- поверхность модуля ---
TABLES, OUT, tables, buckets


===== Scripts\05_search.py (47 строк) =====

--- поверхность модуля ---
MODEL, INDEX_DIR, tokenize, RulesSearch


===== Scripts\06_peek.py (14 строк) =====

--- поверхность модуля ---
path, chunks, idx


===== Scripts\07_find.py (8 строк) =====

--- поверхность модуля ---
pat


===== Scripts\09_fix_mojibake.py (27 строк) =====

--- поверхность модуля ---
fix


===== Scripts\11_normalize_tables.py (313 строк) =====

--- поверхность модуля ---
ROOT, TABLES, BLOCKS, OUT, REVIEW, OLLAMA, MODEL, LLM_FAMILIES, SPECS, slug, flat, digits, ints, flat_cells, validate, unwrap, spec_records, parse_weapon, pre_classify, SCHEMAS, SYS, llm_normalize, extract_skill_stats, main


===== Scripts\12_pg_load.py (92 строк) =====

--- поверхность модуля ---
ROOT, DSN_SERVER, DSN_CPR, ensure_database, main


===== Scripts\14_review_fix.py (96 строк) =====

--- поверхность модуля ---
ROOT, REVIEW, OUT, MODEL, OLLAMA, _spec, norm, SYS, call32b, main


===== Scripts\15_export_dataset.py (65 строк) =====

--- поверхность модуля ---
ROOT, DSN, OUT, main


===== Scripts\16_fix_armor_weapons.py (95 строк) =====

--- поверхность модуля ---
ROOT, OUT, slug, write_jsonl, ARMOR_DATA, WEAPONS_DATA, main


===== Scripts\17_rate_last.py (50 строк) =====

--- поверхность модуля ---
DSN, main


===== Scripts\18_extract_lifepath.py (137 строк) =====

--- поверхность модуля ---
LIFEPATH_TABLES, ROLE_LIFEPATH, extract_lifepath


===== Scripts\19_extract_game_data.py (259 строк) =====

--- поверхность модуля ---
script_dir, project_root, DATA_DIR, SKILLS_FULL, WEAPONS_FULL, ARMOR_FULL, CYBERWARE_FULL, MARTIAL_ARTS, MARTIAL_MOVES, save_json, main


===== Scripts\20_extract_enemies.py (217 строк) =====

--- поверхность модуля ---
script_dir, project_root, DATA_DIR, ENEMIES, ENEMY_TIERS, FACTION_ENEMIES, main


===== Scripts\21_extract_factions.py (208 строк) =====

--- поверхность модуля ---
script_dir, project_root, DATA_DIR, FACTIONS, FACTION_TIERS, main


===== Scripts\22_extract_netrunning.py (212 строк) =====

--- поверхность модуля ---
script_dir, project_root, DATA_DIR, CYBERDECKS, PROGRAMS, ARCHITECTURES, main


===== Scripts\23_extract_vehicles.py (182 строк) =====

--- поверхность модуля ---
script_dir, project_root, DATA_DIR, VEHICLES, VEHICLE_CATEGORIES, main


===== Scripts\24_extract_drugs.py (139 строк) =====

--- поверхность модуля ---
script_dir, project_root, DATA_DIR, DRUGS, POISONS, main


===== ИМПОРТЫ backend/engine.py =====
5: import random
6: import json
7: import inspect
8: from backend import combat_rules, rules
9: from pathlib import Path
10: from .wounds import (apply_damage, death_save, get_wound_state,
12: from . import martial
13: from . import netrunning
235: import inspect
237: from backend import rules
379:         from . import vehicles as veh_mod
389:         from . import vehicles as veh_mod
679:     from backend import rules_tables
694:     from backend import rules_tables
