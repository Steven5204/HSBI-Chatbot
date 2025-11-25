import json

def load_rules(filepath="rules.json"):
    """Lädt das Regelwerk als Python-Dict."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def get_general_requirements(rules):
    """Gibt allgemeine Zugangsvoraussetzungen zurück."""
    return rules["Masterstudium_Berufsbegleitend"]["Allgemeine_Zugangsvoraussetzungen"]

def get_programs(rules):
    """Gibt alle Studiengänge mit Anforderungen zurück."""
    return rules["Masterstudium_Berufsbegleitend"]["Studiengänge"]

def get_program_requirements(rules, program_name):
    """Gibt Anforderungen für einen bestimmten Studiengang zurück (oder None)."""
    programmes = get_programs(rules)
    return programmes.get(program_name)