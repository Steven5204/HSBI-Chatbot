from rules_handler import load_rules, get_programs

def test_rules():
    rules = load_rules()
    programmes = get_programs(rules)
    assert "Angewandte_Automatisierung" in programmes
    assert rules["Masterstudium_Berufsbegleitend"]["Allgemeine_Zugangsvoraussetzungen"]["ECTS_Bachelor"] == 210