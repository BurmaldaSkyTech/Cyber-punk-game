"""Добавляет категорию RULE_TEXT: сверка по числам, STAT-якорям и смысловым словам."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
p = ROOT / "tools" / "rules_import.py"
s = p.read_text(encoding="utf-8")

if "def rule_text_ok(" not in s:
    s += '''

RULE_TEXT = {"armor_ablation", "critical_injury_trigger", "rof_rules",
             "melee_opposed_by", "ranged_defense", "autofire_rules",
             "wound_states", "wound_penalties"}
STOP = {"the", "and", "for", "with", "that", "this", "from", "your", "you",
        "are", "can", "any", "all", "its", "into", "upon", "when", "whenever",
        "each", "single", "their", "they", "them", "then", "than", "not",
        "but", "also", "may", "must", "have", "has", "was", "were", "will",
        "would", "should", "could", "how", "many", "times", "amount"}


def rule_text_ok(v, q):
    q = norm(q)
    nums = re.findall(r"\\d+", str(v))
    if nums and not all(n in q for n in nums):
        return False
    for i in re.findall(r"\\b[A-Z]{2,}\\b", str(v)):
        low = i.lower()
        if low in q or any(x in q for x in SYN.get(low, ())):
            continue
        return False
    words = [w.lower() for w in re.findall(r"[A-Za-z]{4,}", str(v))
             if w.lower() not in STOP]
    if not words:
        return True
    return any(w[:5] in q for w in words)
'''
    p.write_text(s, encoding="utf-8")
    print("rules_import: +rule_text_ok")

s = p.read_text(encoding="utf-8")
old = "        ok = formula_ok(val, quote) if key in FORMULA else in_quote(val, quote)"
new = ("        if key in FORMULA:\n"
       "            ok = formula_ok(val, quote)\n"
       "        elif key in RULE_TEXT:\n"
       "            ok = rule_text_ok(val, quote)\n"
       "        else:\n"
       "            ok = in_quote(val, quote)")
if old in s:
    s = s.replace(old, new)
    p.write_text(s, encoding="utf-8")
    print("rules_import: check() использует RULE_TEXT")
else:
    print("rules_import: anchor check() не найден (возможно уже применён)")