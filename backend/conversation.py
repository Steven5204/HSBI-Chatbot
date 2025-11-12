QUESTIONS = [
    "Welchen akademischen Abschluss haben Sie?",
    "Wie viele Jahre Berufserfahrung haben Sie?",
    "Welche Abschlussnote haben Sie in Ihrem Erststudium?",
    "In welchem Bereich sind Sie derzeit tätig?",
    "Möchten Sie in Vollzeit oder berufsbegleitend studieren?"
]

def get_next_question(state):
    """Gibt die nächste Frage basierend auf dem Fortschritt zurück."""
    index = state.get("current_index", 0)
    if index < len(QUESTIONS):
        return QUESTIONS[index]
    else:
        return None

def update_state(state, user_answer):
    """Speichert die Antwort und erhöht den Fortschrittszähler."""
    index = state.get("current_index", 0)
    state[f"answer_{index}"] = user_answer
    state["current_index"] = index + 1
    return state

def summarize_answers(state):
    """Erstellt eine zusammenfassende Darstellung der Eingaben."""
    summary = []
    for i, question in enumerate(QUESTIONS):
        answer = state.get(f"answer_{i}", "Keine Angabe")
        summary.append(f"{question}\n➡️ {answer}")
    return "\n\n".join(summary)
