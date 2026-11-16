"""Собирает бандл для внешней сверки с книгой: текущие константы кода + ключи правил."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from backend import creation, engine, rules

ROOT = pathlib.Path(__file__).resolve().parents[1]

WEAPON_FIELDS = ["damage", "rof", "mag", "price", "skill", "conceal"]
ARMOR_FIELDS = ["sp", "penalty", "price", "conceal"]


def subset(table, fields):
    out = {}
    for k, v in table.items():
        out[k] = {f: v[f] for f in fields if isinstance(v, dict) and f in v}
    return out


if __name__ == "__main__":
    bundle = {
        "task": "Сверить константы кода с Cyberpunk RED Core Rulebook и заполнить ключи правил",
        "book": "Cyberpunk RED Core Rulebook",
        "code_constants": {
            "engine.DV": engine.DV,
            "engine.ARMOR": subset(engine.ARMOR, ARMOR_FIELDS),
            "engine.WEAPONS": subset(engine.WEAPONS, WEAPON_FIELDS),
            "engine.SKILL_STAT": getattr(engine, "SKILL_STAT", {}),
            "creation.limits": creation.limits(),
            "creation.HOUSE": creation.HOUSE,
        },
        "rules_skeleton": {
            pack: sorted(rules.load(pack)["entries"].keys())
            for pack in ["creation", "combat", "armor", "weapons",
                         "cyberware", "netrunning", "gear"]
        },
        "rules_status": rules.status(),
        "output_schema": {
            "book": "Cyberpunk RED Core Rulebook",
            "extractor": "grok",
            "entries": [{"pack": "creation", "key": "stat_pool_edgerunner",
                         "value": "<точное значение из книги>", "page": "<int>",
                         "quote": "<дословная цитата <=200 символов>",
                         "confidence": "high|medium|low"}],
            "not_found": [{"pack": "...", "key": "...", "reason": "..."}],
            "code_discrepancies": [{"symbol": "engine.WEAPONS.heavy_pistol.damage",
                                    "code": "3d6", "book": "3d6", "page": "<int>",
                                    "verdict": "ok|mismatch", "quote": "<=200 символов"}],
        },
    }
    (ROOT / "REVIEW_BUNDLE.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print("REVIEW_BUNDLE.json готов:",
          len(bundle["code_constants"]["engine.WEAPONS"]), "оружий,",
          len(bundle["code_constants"]["engine.ARMOR"]), "бронь,",
          sum(len(v) for v in bundle["rules_skeleton"].values()), "ключей правил")