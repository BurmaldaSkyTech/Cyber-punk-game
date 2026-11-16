import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

TARGETS = {
    "backend/main.py": [
        "CONTRACT_BEATS", "ACT2_SCENE", "ACT3_SCENE",
        "NARR_FLAVOR_SYS", "NARR_HARD_RULES", "JUDGE_SYS",
        "detect_departure_intent", "sanitize_flavor", "assemble_narration",
        "consequences", "suggest_followups", "_act_core", "act",
    ],
    "backend/engine.py": [
        "resolve_check", "resolve_npc_reaction", "_npc_attack_roll",
    ],
}


def dump():
    out = []
    for rel, names in TARGETS.items():
        src = (ROOT / rel).read_text(encoding="utf-8")
        tree = ast.parse(src)
        found = {}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
                found[node.name] = ast.get_source_segment(src, node)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id in names:
                        found[t.id] = ast.get_source_segment(src, node)
        out.append(f"\n\n===== {rel} =====\n")
        for n in names:
            out.append(f"\n--- {n} ---\n{found[n] if n in found else 'NOT FOUND'}\n")
    return "".join(out)


if __name__ == "__main__":
    text = dump()
    (ROOT / "SNAPSHOT.md").write_text(text, encoding="utf-8")
    print(text)