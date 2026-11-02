# scripts/17_extract_lifepath.py
"""Извлечение Lifepath таблиц из corebook (стр. 38-49)."""
import json
from pathlib import Path

LIFEPATH_TABLES = {
    "personality_traits": [
        "Shy and secretive", "Rebellious, antisocial and violent",
        "Arrogant, proud and aloof", "Moody, rash and headstrong",
        "Picky, fussy and nervous", "Stable and serious",
        "Goofy and lighthearted", "Sneaky and deceptive",
        "Intellectual and detached", "Friendly and outgoing",
        "Protective and nurturing", "Driven and passionate"
    ],
    
    "clothing_style": [
        "Generic Chic (standard, colorful)", "Leisurewear (comfort, flexibility)",
        "Urban Flash (flashy, streetwear)", "Businesswear (formal, professional)",
        "High Fashion (exclusive designer)", "Bohemian (vintage, hippie)",
        "Bag Lady Chic (homeless, mismatched)", "Gang Colors (gang-affiliated)",
        "Nomad Leathers (tribal, practical)", "Asia Pop (anime, bright)",
        "Military (camouflage, tactical)", "Rocker Style (leather, studs)"
    ],
    
    "hairstyle": [
        "Mohawk", "Long and ratty", "Short and spiked", "Wild and unkempt",
        "Braided or dreadlocks", "Curly or wavy", "Straight and shoulder-length",
        "Bald or shaved", "Striped or colored", "Mullet or shag",
        "Ponytail or bun", "Short and neat"
    ],
    
    "affectations": [
        "Tattoos (visible, extensive)", "Mirrorshades or cyberoptic implants",
        "Ritual scars or brandings", "Fingerless gloves", "Strange jewelry",
        "Odd contact lenses", "Face paint or makeup", "Spiked bracelets",
        "Elaborate hat or headwear", "Exotic weapon as accessory",
        "Strange pet or drone", "Unusual hairstyle"
    ],
    
    "valued_person": [
        "A parent", "A brother or sister", "A lover or spouse",
        "A close friend", "A mentor or teacher", "A rival or enemy",
        "A child or ward", "A pet", "A celebrity or idol",
        "A gang member", "A corporate contact", "A fixer or dealer"
    ],
    
    "life_goals": [
        "Get rid of a bad reputation", "Gain power and control over others",
        "Get off the street no matter what", "Cause pain and suffering",
        "Live down a past crime", "Hunt down and punish the guilty",
        "Find your true identity", "Clear your name",
        "Make a difference in the world", "Become a legend",
        "Protect the innocent", "Earn respect through skill"
    ],
    
    "friends": [
        "An old girlfriend/boyfriend", "A sibling", "A teacher or mentor",
        "A partner or coworker", "A former enemy turned friend", "A childhood friend",
        "A pet (animal or drone)", "A back alley doc or ripperdoc", "A fixer",
        "A street dealer", "A cop or lawman", "A gang member"
    ],
    
    "enemies": [
        "An ex-friend", "An ex-lover", "An estranged family member",
        "A rival professional", "A corporate enemy", "A gang rival",
        "A government agency", "A street punk you humiliated", "A booster-ganger",
        "A hunter or bounty hunter", "A corporate assassin", "A rogue AI or netrunner"
    ],
    
    "tragic_love": [
        "Your lover died in an accident", "Your lover was murdered",
        "Your lover vanished without explanation", "Your lover went insane or cyberpsycho",
        "A rival cut you out", "Your lover was kidnapped or blackmailed",
        "Your lover betrayed you for money", "Your lover turned out to be a spy",
        "Your lover was arrested or imprisoned", "Your lover was drafted or deployed",
        "Your lover was killed in a corporate hit", "You were forced to leave your lover"
    ],
    
    "lovers": [
        "A prostitute or street person", "A corporate executive", "A gang member",
        "A rockerboy or media", "A nomad", "A fixer or dealer",
        "A netrunner or techie", "A solo or mercenary", "A cop or lawman",
        "A doctor or medtech", "A student or academic", "A celebrity or idol"
    ],
}

# Role-specific lifepath (пример для Solo, можно расширить)
ROLE_LIFEPATH = {
    "Solo": {
        "who_did_you_work_for": [
            "A corporation", "A mob boss", "A city government",
            "A street gang", "A nomad clan", "A fixer",
            "A media", "A private detective", "Yourself (freelance)",
            "A military organization", "A political faction", "A secret society"
        ],
        "moral_alignment": [
            "Strictly honorable: never betray a client", "Professional: do the job, ask no questions",
            "Mercenary: work for the highest bidder", "Vigilante: protect the innocent",
            "Criminal: break laws without remorse", "Idealistic: fight for a cause",
            "Pragmatic: survive at any cost", "Loyal: never abandon allies",
            "Ruthless: eliminate threats preemptively", "Honorable but flexible: bend rules when necessary",
            "Chaotic: enjoy the thrill of danger", "Redemptive: atone for past sins"
        ],
        "partner_fate": [
            "They died in a job gone wrong", "They betrayed you and disappeared",
            "They retired to a quiet life", "They became a rival",
            "They were arrested and imprisoned", "They went cyberpsycho",
            "They vanished on a job", "They were killed by a corporate hit",
            "They joined a gang", "They became a fixer",
            "They're still working with you", "You don't know what happened to them"
        ],
    },
    # Можно добавить для других ролей
}

def extract_lifepath():
    """Сохраняет Lifepath таблицы в JSON."""
    # Абсолютный путь: от скрипта поднимаемся на 2 уровня (scripts/ → корень)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output = project_root / "data" / "normalized" / "lifepath_tables.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "general": LIFEPATH_TABLES,
        "role_specific": ROLE_LIFEPATH
    }
    
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Extracted {len(LIFEPATH_TABLES)} general lifepath tables")
    print(f"Extracted {len(ROLE_LIFEPATH)} role-specific lifepath tables")
    print(f"Saved to {output}")

if __name__ == "__main__":
    extract_lifepath()