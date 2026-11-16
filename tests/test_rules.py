def test_get_optional_never_raises(tmp_path, monkeypatch):
    from backend import rules
    monkeypatch.setattr(rules, "RULES_DIR", tmp_path)
    rules._CACHE.clear()
    rules.skeleton("combat", ["range_dv"])
    assert rules.get_optional("combat", "range_dv") is None
    assert rules.get_optional("combat", "range_dv", default={"close": 13}) == {"close": 13}


def test_resolve_check_works_with_unverified_rules(tmp_path, monkeypatch):
    from backend import engine, rules
    monkeypatch.setattr(rules, "RULES_DIR", tmp_path)
    rules._CACHE.clear()
    rules.skeleton("creation", ["skill_list"])
    rules.skeleton("combat", ["dv_table", "wound_penalties", "range_dv", "ranged_defense"])
    st = {"npcs": [{"id": "g1", "name": "Guard", "hp": 20, "max_hp": 20, "armor": "kevlar"}],
          "threat": None}
    actor = {"name": "V", "stats": {"REF": 7}, "skills": {"handgun": 4}, "hp": 12, "max_hp": 12}
    mech = engine.resolve_check(st, actor, {"action_type": "attack_ranged", "skill": "handgun",
                                            "dv_key": "difficult", "target": "g1",
                                            "_text": "shoot the guard"})
    assert mech["stat_key"] == "REF"
    assert isinstance(mech["total"], int)