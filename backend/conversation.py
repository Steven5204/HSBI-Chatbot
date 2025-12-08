from rules_excel import load_excel_rules, calculate_bachelor_ects

# Lade Regelwerk aus Excel (nur einmal beim Start)
try:
    RULES = load_excel_rules("zulassung.xlsx")
except Exception as e:
    print(f"[WARN] Excel-Regeln konnten nicht geladen werden: {e}")
    RULES = {"Studiengänge": {}, "Allgemein": {}}

questions = [
    {
        "key": "abschlussziel",
        "text": "Für welchen Abschluss interessierst du dich??",
        "options": ["Bachelor", "Master"]
    },

    {
        "key": "hochschulzugang",
        "text": "Besitzt du eine Hochschulzugangsberechtigung (z. B. Abitur, Fachabitur oder eine berufliche Qualifikation)?",
        "options": ["Ja", "Nein"],
        "depends_on": {"abschlussziel": "Bachelor"}
    },

    {
        "key": "hsbi_bachelor",
        "text": "Hast du deinen Bachelor an der HSBI gemacht?",
        "options": ["Ja", "Nein"],
        "depends_on": {"abschlussziel": "Master"}
    },
    {
        "key": "bachelorstudiengang",
        "text": "Welchen Bachelorstudiengang hast du an der HSBI abgeschlossen?",
        "depends_on": {"hsbi_bachelor": "Ja"}
    },
    {
        "key": "bachelorstudiengang",
        "text": "Welchen Studiengang hast du abgeschlossen?",
        "depends_on": {"hsbi_bachelor": "Nein"}
    },
    {
        "key": "studiengang",
        "text": "Für welchen Masterstudiengang interessierst du dich?",
        "options": [
            "Angewandte Automatisierung",
            "Digitale Technologien",
            "Maschinenbau",
            "Wirtschaftsingenieurwesen",
            "Elektrotechnik"
        ],
        "depends_on": {"abschlussziel": "Master"}
    },
    {
        "key": "abschlussnote",
        "text": "Welche Abschlussnote hast du in deinem Vorstudium?",
        "depends_on": {"abschlussziel": "Master"}
    },
    {
        "key": "berufserfahrung",
        "text": "Wie viele Jahre Berufserfahrung hast du nach deinem Vorstudium gesammelt?",
        "depends_on": {"abschlussziel": "Master"}
    },
    {
        "key": "englischkenntnisse",
        "text": "Besitzt du Englischkenntnisse auf mindestens B2-Niveau?",
        "options": ["Ja", "Nein"],
        "depends_on": {"abschlussziel": "Master"}
    }
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
    """
    Gibt die nächste passende Frage basierend auf dem aktuellen Gesprächsstatus zurück.
    """
    # Wenn Abschlussziel noch nicht gewählt → zuerst danach fragen
    if "abschlussziel" not in state:
        return {
            "key": "abschlussziel",
            "text": "Für welchen Abschluss interessieren Sie sich?",
            "options": ["Bachelor", "Master"]
        }

    # 🟦 Wenn Bachelor → frage nach Hochschulzugangsberechtigung
    if state["abschlussziel"].lower() == "bachelor" and "hochschulzugang" not in state:
        return {
            "key": "hochschulzugang",
            "text": "Besitzen Sie eine Hochschulzugangsberechtigung (z. B. Abitur, Fachabitur oder eine berufliche Qualifikation)?",
            "options": ["Ja", "Nein"]
        }

    # 🟨 Wenn Master → führe bisherigen Fragefluss aus
    if state["abschlussziel"].lower() == "master":
        # z. B. Fragen wie hsbi_bachelor, bachelorstudiengang, studiengang usw.
        for q in questions:
            if "depends_on" in q:
                key, value = list(q["depends_on"].items())[0]
                if state.get(key, "").lower() != value.lower():
                    continue  # Bedingung nicht erfüllt → überspringen

            # Nur unbeantwortete Fragen anzeigen
            if q["key"] not in state:
                return q

    # Wenn alle Fragen beantwortet → keine mehr
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
        # 🔹 Wenn der Nutzer einen HSBI-Bachelor hat → prüfe, ob ECTS berechnet werden können
    if state.get("hsbi_bachelor") == "Ja":
        required_keys = ["bachelorstudiengang", "studienart", "vertiefung"]

        # Wenn alle drei Angaben vorhanden sind
        if all(key in state for key in required_keys):
            from rules_excel import calculate_bachelor_ects
            try:
                ects_data = calculate_bachelor_ects(
                    state["bachelorstudiengang"],
                    state["studienart"],
                    state["vertiefung"]
                )
                if ects_data:
                    state["ects_ist"] = ects_data
                    print(f"[ECTS-Berechnung erfolgreich]: {ects_data}")
                else:
                    print("[ECTS-Berechnung] Keine Daten gefunden für diese Kombination.")
            except Exception as e:
                print(f"[Fehler bei ECTS-Berechnung]: {e}")
        
    return state
