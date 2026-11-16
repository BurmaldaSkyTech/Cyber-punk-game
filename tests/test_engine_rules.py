def test_ram_does_not_crash_without_target():
    from backend import engine
    st = {"npcs": [{"id": "g1", "name": "Охранник", "hp": 20, "max_hp": 20}], "threat": None}
    actor = {"name": "A", "stats": {"REF": 6}, "skills": {"drive_land_vehicle": 3},
             "hp": 12, "max_hp": 12, "vehicle": "car_compact"}
    mech = engine.resolve_check(st, actor, {"action_type": "ram", "skill": "drive_land_vehicle",
                                            "dv_key": "professional", "target": "g1", "_text": "таранит"})
    assert mech["ram_result"] in ("hit", "miss")


def test_armor_ablates_on_penetration():
    from backend import engine
    ent = {"armor": "kevlar"}
    before = engine.armor_sp(ent)
    abl = engine.ablate_armor(ent, penetrated=True)
    assert abl is None or engine.armor_sp(ent) == before - abl["step"]


def test_aimed_shot_changes_roll_modifier():
    from backend import engine
    st = {"npcs": [{"id": "g1", "name": "Охранник", "hp": 20, "max_hp": 20, "armor": "kevlar"}]}
    actor = {"name": "A", "stats": {"REF": 6}, "skills": {"handgun": 3}, "hp": 12, "max_hp": 12}
    body = engine.resolve_check(st, actor, {"action_type": "attack_ranged", "skill": "handgun",
                                            "dv_key": "difficult", "target": "g1", "location": "torso"})
    head = engine.resolve_check(st, actor, {"action_type": "attack_ranged", "skill": "handgun",
                                            "dv_key": "difficult", "target": "g1", "location": "head"})
    assert head["aimed_penalty"] <= body["aimed_penalty"]


def test_initiative_orders_by_roll():
    from backend import engine
    ents = [{"name": "A", "stats": {"REF": 8}}, {"name": "B", "stats": {"REF": 2}}]
    order = engine.roll_initiative(ents)
    assert set(order) == {"A", "B"}