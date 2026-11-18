import pytest
from backend import creation


def _stats(o):
    return {k: 6 for k in o["stats"]}


def _base(o):
    return {s["key"]: s["baseline"] for s in o["skills"] if s["baseline"]}


def test_skill_pool_is_delta():
    o = creation.options("Solo", "edgerunner")
    sk = _base(o)
    sk["handgun"] = 6
    ch = creation.build({"role": "Solo", "method": "edgerunner",
                         "stats": o["template_stats"], "skills": sk})
    assert ch["purchase_log"]["skill_points_spent"] == 2


def test_purchase_spends_budget():
    o = creation.options("Solo", "complete_package")
    ch = creation.build({"role": "Solo", "method": "complete_package",
                         "stats": _stats(o), "purchases": ["shotgun"]})
    assert ch["eb"] == o["budget"] - 500
    assert "shotgun" in ch["inventory"]


def test_overspend_rejected():
    o = creation.options("Solo", "complete_package")
    with pytest.raises(ValueError):
        creation.build({"role": "Solo", "method": "complete_package",
                        "stats": _stats(o),
                        "purchases": ["shotgun", "assault_rifle", "sniper_rifle",
                                      "Sandevistan", "Kerenzikov"]})


def test_martial_form_required():
    o = creation.options("Solo", "edgerunner")
    sk = _base(o)
    sk["martial_arts"] = 2
    spec = {"role": "Solo", "method": "edgerunner",
            "stats": o["template_stats"], "skills": sk}
    with pytest.raises(ValueError):
        creation.build(spec)
    spec["martial_form"] = "Judo"
    assert creation.build(spec)["martial_form"] == "Judo"


def test_full_skill_list():
    assert len(creation.options("Solo")["skills"]) > 40