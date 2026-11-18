from backend import wounds_book as w


def test_even_max_threshold():
    assert w.get_wound_state(20, 40) == "lightly"
    assert w.get_wound_state(19, 40) == "seriously"
    assert w.get_wound_state(0, 40) == "mortally"


def test_crit_only_on_flag():
    t = {"hp": 5, "max_hp": 40}
    assert w.apply_damage(t, 3)["critical_injury"] is None
    assert w.apply_damage(t, 3, crit=True)["critical_injury"] is not None


def test_death_save_penalty_accumulates():
    t = {"stats": {"BODY": 6}}
    w.death_save(t)
    assert t["death_save_penalty"] == 1


def test_mortal_move_penalty():
    t = {"hp": 1, "max_hp": 40}
    r = w.apply_damage(t, 5)
    assert r["wound_state"] == "mortally"
    assert r["move_penalty"] <= r["penalty"]


def test_net_mu_is_int():
    from backend import netrunning as n
    st = n.calculate_net_stats({"stats": {"INT": 6}, "programs": ["see_ya"]})
    assert isinstance(st["mu_used"], int)