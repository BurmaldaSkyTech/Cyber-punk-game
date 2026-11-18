def test_head_multiplier_applies_after_armor():
    from backend import combat_rules
    assert combat_rules.aimed_multiplier("head") == 2
    assert combat_rules.aimed_multiplier("torso") == 1
    raw, sp = 8, 7
    assert max(0, raw - sp) * combat_rules.aimed_multiplier("head") == 2


def test_wound_thresholds_book():
    from backend import combat_rules as c
    assert c.wound_state(35, 35) == "unharmed"
    assert c.wound_state(34, 35) == "lightly"
    assert c.wound_state(17, 35) == "seriously"
    assert c.wound_state(0, 35) == "mortally"


def test_death_save_accumulates_and_ten_fails():
    from backend import combat_rules as c
    ent = {"stats": {"BODY": 6}}
    c.death_save(ent)
    assert ent["death_save_penalty"] == 1


def test_edgerunner_has_no_stat_pool():
    from backend import creation
    assert creation.limits("edgerunner")["stat_pool"] is None
    assert creation.limits("complete_package")["stat_pool"] == 62