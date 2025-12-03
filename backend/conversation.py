from rules_excel import load_excel_rules, get_program_requirements, get_general_requirements

# Regelwerk laden (einmalig beim Start)
RULES = load_excel_rules("zulassung.xlsx")

def get_next_question(state):
    """Bestimmt die nächste sinnvolle Frage basierend auf dem aktuellen Zustand."""
    questions = [
        {
            "key": "studiengang",
            "text": "Für welchen Masterstudiengang interessieren Sie sich?",
            "options": [
                "Angewandte Automatisierung",
                "Digitale Technologien",
                "Wirtschaftsingenieurwesen",
                "Maschinenbau"
            ],
        },
        {
            "key": "abschluss",
            "text": "Welchen akademischen Abschluss haben Sie?",
            "options": ["Bachelor", "Diplom", "Staatsexamen", "Sonstiges"],
        },
        {
            "key": "berufserfahrung_jahre",
            "text": "Wie viele Jahre einschlägige Berufserfahrung haben Sie nach Ihrem Abschluss?",
        },
        {
            "key": "abschlussnote",
            "text": "Welche Abschlussnote haben Sie im Bachelor?",
        },
        {
            "key": "englischkenntnisse",
            "text": "Wie würden Sie Ihre Kenntnisse im technischen Englisch bewerten?",
            "options": ["Sehr gut", "Gut", "Befriedigend", "Ausreichend", "Mangelhaft"],
        },
    ]

    # Wenn Studiengang gewählt wurde, aber ECTS-Info noch nicht gezeigt wurde
    if "studiengang" in state and not state.get("ects_info_shown"):
        program = state["studiengang"]
        reqs = get_program_requirements(RULES, program)
        if reqs:
            ects_reqs = reqs.get("ECTS_Anforderungen", {})
            ects_info = "\n".join([f"- {k}: {v} ECTS" for k, v in ects_reqs.items()])
            info_message = (
                f"ℹ️ Für den Studiengang **{program}** gelten folgende fachlichen Mindestanforderungen:\n"
                f"{ects_info}\n\nDiese werden im Rahmen Ihrer Bewerbung durch den Studierendenservice geprüft."
            )
            state["ects_info_shown"] = True
            return info_message

    # Nächste reguläre Frage finden
    for q in questions:
        if q["key"] not in state:
            text = q["text"]
            if "options" in q:
                opts = "\n".join([f"- {o}" for o in q["options"]])
                text += f"\n\nAntwortmöglichkeiten:\n{opts}"
            return text

    # Alle Fragen beantwortet -> zur Zusammenfassung übergehen
    return None


def update_state(state, user_input):
    """Speichert die Antwort des Nutzers für die aktuelle Frage."""
    keys = [
        "studiengang",
        "abschluss",
        "berufserfahrung_jahre",
        "abschlussnote",
        "englischkenntnisse",
    ]
    for key in keys:
        if key not in state:
            state[key] = user_input
            break
    return state


def summarize_answers(state):
    """Erstellt eine textuelle Zusammenfassung der bisherigen Angaben."""
    summary = (
        f"Studiengang: {state.get('studiengang', '–')}\n"
        f"Abschluss: {state.get('abschluss', '–')}\n"
        f"Berufserfahrung (Jahre): {state.get('berufserfahrung_jahre', '–')}\n"
        f"Abschlussnote: {state.get('abschlussnote', '–')}\n"
        f"Technisches Englisch: {state.get('englischkenntnisse', '–')}\n"
    )
    return summary
