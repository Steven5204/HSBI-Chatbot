from rules_excel import load_excel_rules

# Lade Regelwerk aus Excel (nur einmal beim Start)
try:
    RULES = load_excel_rules("zulassung.xlsx")
except Exception as e:
    print(f"[WARN] Excel-Regeln konnten nicht geladen werden: {e}")
    RULES = {"Studiengänge": {}, "Allgemein": {}}

questions = [
    {"key": "abschlussziel", "text": "Für welchen Abschluss interessieren Sie sich?",
     "options": ["Bachelor", "Master"]},

    {"key": "hochschulzugang", "depends_on": {"abschlussziel": "Bachelor"},
     "text": "Welche Hochschulzugangsberechtigung haben Sie?",
     "options": [
         "Allgemeine Hochschulreife",
         "Fachhochschulreife",
         "Fachgebundene Hochschulreife",
         "Berufliche Qualifizierung",
         "Ausländische Hochschulzugangsberechtigung"
     ]},

    {"key": "bachelor_hinweis", "depends_on": {"abschlussziel": "Bachelor"},
     "text": "Danke! Ich prüfe Ihren Zugang basierend auf Ihrer Hochschulzugangsberechtigung."},

    {"key": "master_typ", "depends_on": {"abschlussziel": "Master"},
     "text": "Haben Sie Ihren Bachelor an der HSBI gemacht?",
     "options": ["Ja", "Nein"]},

    {
    "key": "bachelor_hsbi",
    "depends_on": {"master_typ": "Ja"},
    "text": "Welchen Bachelorstudiengang haben Sie an der HSBI abgeschlossen?",
    "options": list(RULES.get("Studiengänge", {}).keys()) or [
        "Digitale Technologien", "Maschinenbau", "Wirtschaftsingenieurwesen"
        ]
    }, 

    {"key": "studiengang", "depends_on": {"abschlussziel": "Master"},
     "text": "Für welchen Masterstudiengang interessieren Sie sich?",
     "options": list(RULES.get("Studiengänge", {}).keys()) or
                ["Angewandte Automatisierung", "Digitale Technologien", "Wirtschaftsingenieurwesen", "Maschinenbau"]},

    {"key": "abschlussnote", "depends_on": {"abschlussziel": "Master"},
     "text": "Welche Abschlussnote haben Sie im Bachelor?"},

    {"key": "berufserfahrung_jahre", "depends_on": {"abschlussziel": "Master"},
     "text": "Wie viele Jahre Berufserfahrung haben Sie nach Ihrem Bachelor gesammelt?"},

    {"key": "englischkenntnisse", "depends_on": {"abschlussziel": "Master"},
     "text": "Wie beurteilen Sie Ihre technischen Englischkenntnisse?",
     "options": ["Sehr gut", "Gut", "Befriedigend", "Ausreichend", "Mangelhaft"]}
]

def get_ects_info(state, rules):
    if "studiengang" not in state or state.get("ects_info_shown"):
        return None
    program = state["studiengang"]
    reqs = rules["Studiengänge"].get(program)
    if not reqs:
        return None
    ects_reqs = reqs["ECTS_Anforderungen"]
    ects_info = "\n".join([f"- {k}: {v} ECTS" for k, v in ects_reqs.items()])
    state["ects_info_shown"] = True
    return f"ℹ️ Für den Studiengang **{program}** gelten folgende Anforderungen:\n{ects_info}"

def get_next_question(state):
    for q in questions:
        if "depends_on" in q:
            if any(state.get(k) != v for k, v in q["depends_on"].items()):
                continue
        if q["key"] not in state:
            return q
    return None

def update_state(state, user_input):
    if user_input.lower() in ["ok", "weiter", "next"]:
        return state
    for q in questions:
        if "depends_on" in q:
            if any(state.get(k) != v for k, v in q["depends_on"].items()):
                continue
        if q["key"] not in state:
            state[q["key"]] = user_input
            if q["key"] == "abschlussziel":
                state["nutzerkategorie"] = "bachelor" if user_input == "Bachelor" else None
            if q["key"] == "master_typ":
                state["nutzerkategorie"] = "master_intern" if user_input == "Ja" else "master_extern"
            return state
    return state
