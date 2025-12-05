from rules_excel import load_excel_rules, get_program_requirements, get_general_requirements

# Regelwerk laden (einmalig beim Start)
RULES = load_excel_rules("zulassung.xlsx")

# ----------------------------------------
# Fragenlogik
# ----------------------------------------
questions = [

    # 1) Hauptklassifikation
    {
        "key": "abschlussziel",
        "text": "Für welchen Abschluss interessieren Sie sich?",
        "options": ["Bachelor", "Master"]
    },

    # -------------------------
    # BACHELOR-FRAGEN
    # -------------------------
    {
        "key": "hochschulzugang",
        "depends_on": {"abschlussziel": "Bachelor"},
        "text": "Welche Hochschulzugangsberechtigung haben Sie?",
        "options": [
            "Allgemeine Hochschulreife",
            "Fachhochschulreife",
            "Fachgebundene Hochschulreife",
            "Berufliche Qualifizierung",
            "Ausländische Hochschulzugangsberechtigung"
        ]
    },

    {
        "key": "bachelor_hinweis",
        "depends_on": {"abschlussziel": "Bachelor"},
        "text": "Danke! Ich prüfe Ihren Zugang basierend auf Ihrer Hochschulzugangsberechtigung."
        # reine Info
    },

    # -------------------------
    # MASTER-FRAGEN
    # -------------------------
    {
        "key": "master_typ",
        "depends_on": {"abschlussziel": "Master"},
        "text": "Haben Sie Ihren Bachelor an der HSBI gemacht?",
        "options": ["Ja", "Nein"]
    },

    {
        "key": "studiengang",
        "depends_on": {"abschlussziel": "Master"},
        "text": "Für welchen Masterstudiengang interessieren Sie sich?",
        "options": [
            "Angewandte Automatisierung",
            "Digitale Technologien",
            "Wirtschaftsingenieurwesen",
            "Maschinenbau"
        ]
    },

    {
        "key": "abschlussnote",
        "depends_on": {"abschlussziel": "Master"},
        "text": "Welche Abschlussnote haben Sie im Bachelor?"
    },

    {
        "key": "berufserfahrung_jahre",
        "depends_on": {"abschlussziel": "Master"},
        "text": "Wie viele Jahre Berufserfahrung haben Sie nach Ihrem Bachelor gesammelt?"
    },

    {
        "key": "englischkenntnisse",
        "depends_on": {"abschlussziel": "Master"},
        "text": "Wie beurteilen Sie Ihre technischen Englischkenntnisse?",
        "options": ["Sehr gut", "Gut", "Befriedigend", "Ausreichend", "Mangelhaft"]
    }
]


# ----------------------------------------
# ECTS-INFO wird NICHT in get_next_question zurückgegeben!
# ----------------------------------------
# Sie wird in main.py abgefangen und separat als Bot-Nachricht ausgegeben.
# Nur dort darf die Info erscheinen – sonst blockiert sie die Button-Logik.
# ----------------------------------------

def get_ects_info(state, rules):
    if "studiengang" not in state:
        return None
    if state.get("ects_info_shown"):
        return None

    program = state["studiengang"]
    reqs = rules["Studiengänge"].get(program)

    if not reqs:
        return None

    ects_reqs = reqs["ECTS_Anforderungen"]
    ects_info = "\n".join([f"- {k}: {v} ECTS" for k, v in ects_reqs.items()])

    state["ects_info_shown"] = True

    return (
        f"ℹ️ Für den Studiengang **{program}** gelten folgende fachlichen Mindestanforderungen:\n"
        f"{ects_info}\n\nDiese werden im Rahmen Ihrer Bewerbung durch den Studierendenservice geprüft."
    )


# ----------------------------------------
# WICHTIG: get_next_question → immer ein Frageobjekt!
# ----------------------------------------

def get_next_question(state):
    """
    Gibt immer ein Frage-Objekt zurück – KEINEN Text!
    Die ECTS-Info wird NICHT hier generiert.
    """

    for q in questions:
        if not condition_met(state, q):
            continue

        if q["key"] not in state:
            return q  # Frageobjekt mit text + options

    return None


def condition_met(state, question):
    if "depends_on" not in question:
        return True
    for key, value in question["depends_on"].items():
        if state.get(key) != value:
            return False
    return True


def update_state(state, user_input):

    # "OK" NICHT als Antwort speichern
    if user_input.lower() in ["ok", "okay", "weiter", "next"]:
        return state

    for q in questions:
        if not condition_met(state, q):
            continue

        if q["key"] not in state:
            state[q["key"]] = user_input

            if q["key"] == "abschlussziel":
                if user_input == "Bachelor":
                    state["nutzerkategorie"] = "bachelor"
                elif user_input == "Master":
                    state["nutzerkategorie"] = None

            if q["key"] == "master_typ":
                state["nutzerkategorie"] = "master_intern" if user_input == "Ja" else "master_extern"

            return state

    return state


def summarize_answers(state):
    summary = (
        f"Studiengang: {state.get('studiengang', '–')}\n"
        f"Abschluss: {state.get('abschluss', '–')}\n"
        f"Berufserfahrung (Jahre): {state.get('berufserfahrung_jahre', '–')}\n"
        f"Abschlussnote: {state.get('abschlussnote', '–')}\n"
        f"Technisches Englisch: {state.get('englischkenntnisse', '–')}\n"
    )
    return summary


def count_relevant_questions(state, questions):
    return sum(
        1
        for q in questions
        if "depends_on" not in q or all(state.get(k) == v for k, v in q["depends_on"].items())
    )
