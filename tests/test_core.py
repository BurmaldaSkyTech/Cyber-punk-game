# tests/test_core.py
import importlib.util, random, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import engine

_spec = importlib.util.spec_from_file_location("norm", ROOT / "scripts" / "11_normalize_tables.py")
norm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(norm)


def test_d10_chain_up(monkeypatch):
    seq = iter([10, 10, 3])
    monkeypatch.setattr(random, "randint", lambda a, b: next(seq))
    assert engine.roll_d10() == (10, 23)


def test_d10_chain_down(monkeypatch):
    seq = iter([1, 1, 4])
    monkeypatch.setattr(random, "randint", lambda a, b: next(seq))
    assert engine.roll_d10() == (1, -4)


def test_parse_dice(monkeypatch):
    seq = iter([3, 6, 6])
    monkeypatch.setattr(random, "randint", lambda a, b: next(seq))
    total, faces = engine.roll_dice("3d6")
    assert faces == [3, 6, 6] and total == 15


def test_wound_state():
    assert engine.wound_state(12, 12) == "unharmed"
    assert engine.wound_state(11, 12) == "lightly"
    assert engine.wound_state(5, 12) == "seriously"
    assert engine.wound_state(0, 12) == "mortally"


def test_dv_keys_guard():
    assert set(engine.DV) >= {"simple", "everyday", "difficult",
                              "professional", "heroic", "incredible", "legendary"}


def test_resolve_attack(monkeypatch):
    seq = iter([5, 4, 6])
    monkeypatch.setattr(random, "randint", lambda a, b: next(seq))
    state = {"npcs": [{"id": "g1", "name": "Guard", "hp": 20, "max_hp": 20,
                       "wound": "unharmed", "armor": "kevlar"}], "threat": None}
    actor = {"name": "V", "stats": {"REF": 7}, "skills": {"handgun": 4}, "wound": "unharmed"}
    judge = {"action_type": "attack_ranged", "skill": "handgun", "dv_key": "difficult",
             "weapon": "medium_pistol", "target": "g1", "_text": "shoot the guard"}
    m = engine.resolve_check(state, actor, judge)
    assert m["dv"] == 15 and m["total"] == 16 and m["success"]
    assert m["armor_sp"] == 7 and m["net_damage"] == 3
    assert state["npcs"][0]["hp"] == 17


def test_validate_verbatim():
    md = "| Weapon | Damage |\n|---|---|\n| Heavy Pistol | 3d6 |"
    assert norm.validate([{"name": "Heavy Pistol", "damage": "3d6"}], md) == []
    assert norm.validate([{"name": "Heavy Pistol", "damage": "4d6"}], md) != []


def test_unwrap_dv():
    md = ("| Difficulty | Simple | Everyday | Difficult |\n|---|---|---|---|\n"
          "| Description | a | b | c |\n| DV | 9 | 13 | 15 |")
    rows, note = norm.spec_records(md, norm.SPECS["dv_table"])
    assert len(rows) == 3 and norm.ints(rows[2]["dv"]) == 15


def test_clean_cjk():
    from backend.common import clean
    assert clean("privet 掩码 mir") == "privet mir"


def test_no_mojibake_in_chunks():
    p = ROOT / "data" / "chunks" / "chunks.jsonl"
    if not p.exists():
        pytest.skip("chunks not built")
    bad = sum(1 for l in open(p, encoding="utf-8") if "â–" in l)
    assert bad == 0, "mojibake in chunks: run 09_fix_mojibake.py + 03_index.py"