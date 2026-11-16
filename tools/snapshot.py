import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

TARGETS = {
    "backend/main.py": [
        "CONTRACT_BEATS", "ACT2_SCENE", "ACT3_SCENE", "LOCATION_RU",
        "NARR_FLAVOR_SYS", "NARR_HARD_RULES", "JUDGE_SYS",
        "ACCEPT_WORDS", "ACT2_TRIGGERS_WORDS", "NEG_DEPARTURE",
        "CONFIRM_YES", "CONFIRM_NO",
        "detect_departure_intent", "_clean_flavor", "sanitize_flavor",
        "_attack_outcome_lines", "assemble_narration", "consequences",
        "handover_contract", "apply_world_ticks", "suggest_followups",
        "_act_core", "act",
        "chargen_endpoint", "creation_options", "creation_build",
        "lobby_create", "lobby_join", "lobby_start", "ws_endpoint",
        "get_state", "persist", "public_state", "broadcast_now",
    ],
    "backend/engine.py": [
        "resolve_check", "resolve_npc_reaction", "_npc_attack_roll",
        "_is_hostile", "_npc_weapon_key",
    ],
    "backend/creation.py": [
        "ROLE_ALIASES", "ROLES", "STATS", "SKILLS", "GEAR", "PROGRAMS",
        "ROLE_PRESETS", "normalize_role", "preset",
        "random_character", "options", "build",
    ],
}

JS_TARGETS = {
    "static/index.html": [
        "renderLogEntry", "syncLog", "connectWS", "send",
        "cbLoad", "cbBuild", "confirmChar", "doCreate", "doJoin",
    ],
}


def py_blocks(src, names):
    tree = ast.parse(src)
    found = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            found[node.name] = ast.get_source_segment(src, node)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in names:
                    found[t.id] = ast.get_source_segment(src, node)
    return found


def js_blocks(src, names):
    found = {}
    for name in names:
        m = re.search(r"(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", src)
        if not m:
            continue
        i = src.find("{", m.end())
        if i < 0:
            continue
        depth, j = 0, i
        while j < len(src):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        found[name] = src[m.start():j + 1]
    return found


def dump():
    out, stats = [], []
    for rel, names in TARGETS.items():
        path = ROOT / rel
        out.append(f"\n\n===== {rel} =====\n")
        if not path.exists():
            out.append("FILE NOT FOUND\n")
            stats.append((rel, 0, len(names)))
            continue
        src = path.read_text(encoding="utf-8")
        found = py_blocks(src, names)
        for n in names:
            out.append(f"\n--- {n} ---\n{found[n] if n in found else 'NOT FOUND'}\n")
        stats.append((rel, len(found), len(names)))

    for rel, names in JS_TARGETS.items():
        path = ROOT / rel
        out.append(f"\n\n===== {rel} =====\n")
        if not path.exists():
            out.append("FILE NOT FOUND\n")
            stats.append((rel, 0, len(names)))
            continue
        src = path.read_text(encoding="utf-8")
        found = js_blocks(src, names)
        for n in names:
            out.append(f"\n--- {n} ---\n{found[n] if n in found else 'NOT FOUND'}\n")
        stats.append((rel, len(found), len(names)))

    return "".join(out), stats


if __name__ == "__main__":
    text, stats = dump()
    dest = ROOT / "SNAPSHOT.md"
    dest.write_text(text, encoding="utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print(f"SNAPSHOT.md written: {len(text)} chars -> {dest}")
    for rel, got, total in stats:
        print(f"  {rel}: {got}/{total} blocks")
    if "--print" in sys.argv:
        print(text)