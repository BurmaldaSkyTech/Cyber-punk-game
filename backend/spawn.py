# backend/spawn.py
"""Спавн врагов из шаблонов enemies.json в сцену."""
import json
from pathlib import Path

_data_dir = Path(__file__).parent.parent / "data" / "normalized"


def _load():
    p = _data_dir / "enemies.json"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"enemies": {}, "tiers": {}, "faction_enemies": {}}


ENEMY_DATA = _load()


def get_template(template_id):
    """Возвращает шаблон врага."""
    return ENEMY_DATA.get("enemies", {}).get(template_id)


def make_enemy(template_id, uid):
    """Создаёт NPC из шаблона."""
    t = get_template(template_id)
    if not t:
        return None
    return {
        "id": uid,
        "name": t["name"],
        "template": template_id,
        "hp": t["hp"], "max_hp": t["hp"],
        "wound": "unharmed", "dead": False,
        "armor": t["armor"],
        "weapon": t["weapon"],
        "stats": dict(t["stats"]),
        "skills": dict(t["skills"]),
        "behavior": t.get("behavior", ""),
        "faction": t.get("faction", ""),
        "special": t.get("special", ""),
    }


def spawn_group(state, template_id, count, prefix="enemy"):
    """Добавляет группу врагов в state['npcs']. Возвращает список id."""
    spawned = []
    existing = len([n for n in state.get("npcs", [])
                    if n.get("template") == template_id])
    for i in range(count):
        num = existing + i + 1
        uid = f"{prefix}{num}"
        npc = make_enemy(template_id, uid)
        if npc:
            if count > 1:
                npc["name"] = f"{npc['name']} #{num}"
            state.setdefault("npcs", []).append(npc)
            spawned.append(uid)
    return spawned


def npc_context(state):
    """Строки с поведением и фракциями NPC для нарратора."""
    lines = []
    for n in state.get("npcs", []):
        if n.get("dead"):
            continue
        line = f"- {n['name']}: HP {n['hp']}/{n['max_hp']}, броня {n.get('armor', 'нет')}"
        if n.get("behavior"):
            line += f", поведение: {n['behavior']}"
        if n.get("faction"):
            line += f", фракция: {n['faction']}"
        if n.get("special"):
            line += f", особенность: {n['special']}"
        lines.append(line)
    return "\n".join(lines)