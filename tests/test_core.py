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
    # Проверяем только удаление CJK (китайские иероглифы)
    assert clean("привет 掩码 мир") == "привет мир"


def test_clean_latin():
    from backend.common import clean
    # Проверяем удаление латинских слов из русского текста
    assert clean("привет hello мир") == "привет мир"
    assert clean("пластины armorjack искры") == "пластины искры"

def test_chargen_random_valid():
    from backend import chargen
    for seed in range(20):
        ch = chargen.random_character(seed=seed)
        assert chargen.validate_character(ch) == []
        assert sum(ch["stats"].values()) == 62
        assert ch["hp"] == ch["stats"]["BODY"] * 2


def test_chargen_validate_catches_cheat():
    from backend import chargen
    ch = chargen.random_character(seed=1)
    ch["stats"]["BODY"] = 9
    assert chargen.validate_character(ch) != []

def test_chargen_random_valid():
    from backend import chargen
    for seed in range(20):
        ch = chargen.random_character(seed=seed)
        assert chargen.validate_character(ch) == []
        assert sum(ch["stats"].values()) == 62
        assert ch["hp"] == ch["stats"]["BODY"] * 2
        assert "Neural Link" in ch["cyberware"]
        assert ch["eb"] > 0
        assert "cultural_origins" in ch["lifepath"]


def test_chargen_validate_catches_cheat():
    from backend import chargen
    ch = chargen.random_character(seed=1)
    ch["stats"]["BODY"] = 9
    assert chargen.validate_character(ch) != []


def test_chargen_lifepath():
    from backend import chargen
    ch = chargen.random_character(seed=42)
    lp = ch["lifepath"]
    assert "cultural_origins" in lp
    assert "family_background" in lp
    assert "childhood_environment" in lp
    assert "family_crisis" in lp

def test_no_mojibake_in_chunks():
    p = ROOT / "data" / "chunks" / "chunks.jsonl"
    if not p.exists():
        pytest.skip("chunks not built")
    bad = sum(1 for l in open(p, encoding="utf-8") if "â–" in l)
    assert bad == 0, "mojibake in chunks: run 09_fix_mojibake.py + 03_index.py"
 
def test_wound_thresholds():
    from backend.wounds import get_wound_state

    # Здоров только при полном HP
    assert get_wound_state(10, 10) == "unharmed"

    # Больше половины — легко ранен
    assert get_wound_state(9, 10) == "lightly"
    assert get_wound_state(6, 10) == "lightly"

    # Половина или меньше, но больше нуля — серьёзно ранен
    assert get_wound_state(5, 10) == "seriously"
    assert get_wound_state(1, 10) == "seriously"

    # Ноль и ниже — смертельно ранен
    assert get_wound_state(0, 10) == "mortally"
    assert get_wound_state(-1, 10) == "mortally"


def test_wound_penalties():
    from backend.wounds import get_wound_penalty
    
    assert get_wound_penalty("unharmed") == 0
    assert get_wound_penalty("lightly") == 0
    assert get_wound_penalty("seriously") == -2
    assert get_wound_penalty("mortally") == -4


def test_apply_damage():
    from backend.wounds import apply_damage

    # Лёгкий урон: 10 -> 7, это больше половины, значит lightly
    target = {"hp": 10, "max_hp": 10}
    result = apply_damage(target, 3)
    assert result["hp"] == 7
    assert result["wound_state"] == "lightly"
    assert result["penalty"] == 0

    # Серьёзный урон: 5 -> -1, ниже нуля, значит mortally
    target = {"hp": 5, "max_hp": 10}
    result = apply_damage(target, 6)
    assert result["hp"] == -1
    assert result["wound_state"] == "mortally"
    assert result["death_save"] is True

    # Смертельный урон: 1 -> -14
    target = {"hp": 1, "max_hp": 10}
    result = apply_damage(target, 15)
    assert result["hp"] == -14
    assert result["wound_state"] == "mortally"
    assert result["death_save"] is True


def test_death_save():
    from backend.wounds import death_save
    
    target = {"stats": {"BODY": 10}}
    result = death_save(target)
    assert result["roll"] <= 10
    assert result["body"] == 10
    # С BODY 10 никогда не умрёт
    assert result["dead"] is False 