"""Создание персонажа по книге: метод, пакет роли, покупочный бюджет,
навыки приростом от шаблона, форма боевых искусств."""
import random

from backend import creation_catalog as cat
from backend import rules, rules_tables

ROLE_ALIASES = {"techie": "Tech", "tech": "Tech", "netrunner": "Netrunner", "solo": "Solo",
                "rockerboy": "Rockerboy", "fixer": "Fixer", "nomad": "Nomad",
                "medtech": "Medtech", "lawman": "Lawman", "exec": "Exec", "media": "Media"}
METHODS = ("streetrat", "edgerunner", "complete_package")
HANDLES = ["Вектор", "Никс", "Ржавчина", "Спектр", "Кобальт", "Шрам", "Люмен", "Гризли"]


def normalize_role(role):
    roles = rules.get("creation", "roles", house=cat.ROLES)
    if not role:
        return random.choice(roles)
    r = ROLE_ALIASES.get(str(role).strip().lower(), "Solo")
    return r if r in roles else roles[0]


def methods():
    out = {}
    for m in METHODS:
        out[m] = {
            "stat_pool": rules.value_or("creation", f"stat_pool_{m}", None),
            "skill_pool": rules.value_or("creation", f"skill_pool_{m}", 86 if m != "streetrat" else None),
            "stat_verified": rules.verified("creation", f"stat_pool_{m}"),
            "skill_verified": rules.verified("creation", f"skill_pool_{m}"),
        }
    return out


def limits(method="complete_package"):
    m = method if method in METHODS else "complete_package"
    info = methods()[m]
    eb, eb_src = cat.starting_eb(m)
    return {
        "method": m,
        "stat_min": int(rules.get("creation", "stat_min", house=2)),
        "stat_max": int(rules.get("creation", "stat_max", house=8)),
        "stat_pool": info["stat_pool"],
        "skill_pool": info["skill_pool"],
        "skill_max": int(rules.get("creation", "skill_max_at_creation", house=6)),
        "starting_eb": eb, "eb_source": eb_src,
    }


def roll_stats():
    return cat.roll_stats()


def options(role=None, method="complete_package"):
    r = normalize_role(role)
    lim = limits(method)
    tpl = cat.template(r)
    skills = cat.skill_master()
    baseline = {k: int(v) for k, v in tpl["skills"].items() if k in skills}
    package = list(dict.fromkeys([tpl["weapon"], tpl["armor"]] + tpl["gear"] + tpl["cyber"] + tpl["programs"]))
    return {
        "role": r, "roles": rules.get("creation", "roles", house=cat.ROLES),
        "method": lim["method"], "methods": methods(),
        "stats": rules.get("creation", "stat_list", house=list(tpl["stats"].keys())),
        "stat_min": lim["stat_min"], "stat_max": lim["stat_max"], "stat_pool": lim["stat_pool"],
        "template_stats": tpl["stats"],
        "skills": [{"key": k, "stat": s, "baseline": baseline.get(k, 0)} for k, s in sorted(skills.items())],
        "skill_pool": lim["skill_pool"], "skill_max": lim["skill_max"],
        "skill_pool_semantics": "прирост поверх шаблона роли",
        "budget": lim["starting_eb"], "eb_source": lim["eb_source"],
        "package": package, "catalog": cat.catalog(),
        "preset": tpl,
        "martial": cat.martial_options(baseline.get("martial_arts", 0)),
        "sources": {k: rules.provenance("creation", k) for k in
                    ("stat_pool_edgerunner", "stat_pool_complete_package",
                     "skill_pool_edgerunner", "skill_max_at_creation", "hp_formula")},
    }


def _skill_delta(baseline, skills):
    return sum(max(0, int(v) - int(baseline.get(k, 0))) for k, v in skills.items())


def build(spec):
    method = spec.get("method", "complete_package")
    lim = limits(method)
    role = normalize_role(spec.get("role"))
    tpl = cat.template(role)
    stat_keys = rules.get("creation", "stat_list", house=list(tpl["stats"].keys()))

    if lim["stat_pool"] is None:
        base = tpl["stats"] if method == "streetrat" else (spec.get("stats") or cat.roll_stats())
        stats = {k: int(base.get(k, lim["stat_min"])) for k in stat_keys}
    else:
        stats = {k: int(spec.get("stats", {}).get(k, lim["stat_min"])) for k in stat_keys}
        if any(not (lim["stat_min"] <= v <= lim["stat_max"]) for v in stats.values()):
            raise ValueError(f"статы вне диапазона {lim['stat_min']}..{lim['stat_max']}")
        if sum(stats.values()) > lim["stat_pool"]:
            raise ValueError(f"пул статов превышен (макс {lim['stat_pool']})")

    master = cat.skill_master()
    baseline = {k: int(v) for k, v in tpl["skills"].items() if k in master}
    if lim["skill_pool"] is None:
        skills = dict(baseline)
    else:
        skills = {k: int(v) for k, v in (spec.get("skills") or {}).items() if k in master and int(v) > 0}
        for k, v in baseline.items():
            skills[k] = max(skills.get(k, 0), v)
        if any(v > lim["skill_max"] for v in skills.values()):
            raise ValueError(f"навык выше лимита создания {lim['skill_max']}")
        delta = _skill_delta(baseline, skills)
        if delta > lim["skill_pool"]:
            raise ValueError(f"очков навыков потрачено {delta}, доступно {lim['skill_pool']} (прирост поверх шаблона)")

    items = {i["key"]: i for i in cat.catalog()}
    package = list(dict.fromkeys([tpl["weapon"], tpl["armor"]] + tpl["gear"] + tpl["cyber"] + tpl["programs"]))
    bought = [k for k in (spec.get("purchases") or []) if k in items and k not in package]
    cost = sum(items[k]["price"] for k in bought)
    if cost > lim["starting_eb"]:
        raise ValueError(f"не хватает eb: покупки {cost}, бюджет {lim['starting_eb']}")

    owned = list(dict.fromkeys(package + bought))
    cyber = [k for k in owned if k in items and items[k]["category"] == "cyberware"]
    cyber += [c for c in tpl["cyber"] if c not in cyber]
    programs = [k for k in owned if k in items and items[k]["category"] == "program"]
    gear = [k for k in owned if k not in cyber and k not in programs]

    martial = cat.martial_options(skills.get("martial_arts", 0))
    form = spec.get("martial_form")
    if martial["required"] and not form:
        raise ValueError("при навыке martial_arts ≥ 1 нужно выбрать форму боевых искусств")
    if form and form not in martial["forms"]:
        raise ValueError("неизвестная форма боевых искусств")

    weapon = spec.get("weapon") if spec.get("weapon") in owned else tpl["weapon"]
    armor = spec.get("armor") if spec.get("armor") in owned else tpl["armor"]

    from backend import engine
    hp = int(rules_tables.max_hp(stats))
    hl = sum(int(items[c].get("hl", 0)) for c in cyber if c in items)
    humanity = int(stats.get("EMP", 4)) * 10 - hl

    return {
        "name": spec.get("name") or random.choice(HANDLES), "role": role,
        "stats": stats, "skills": skills,
        "hp": hp, "max_hp": hp, "wound": "unharmed", "dsp": 0, "dead": False,
        "armor": armor, "weapon": weapon,
        "eb": lim["starting_eb"] - cost, "humanity": humanity,
        "cyberware": cyber, "inventory": list(dict.fromkeys([weapon, armor] + gear)),
        "programs": programs, "active_effects": [],
        "martial_form": form, "creation_method": lim["method"],
        "purchase_log": {"budget": lim["starting_eb"], "spent": cost, "bought": bought,
                         "package": package, "skill_points_spent": _skill_delta(baseline, skills)},
    }


def random_character(role=None, name=None):
    r = normalize_role(role)
    tpl = cat.template(r)
    return build({"name": name or random.choice(HANDLES), "role": r,
                  "method": "streetrat", "stats": tpl["stats"], "skills": tpl["skills"],
                  "purchases": [], "martial_form": None})