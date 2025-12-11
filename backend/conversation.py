from rules_excel import load_excel_rules, calculate_bachelor_ects, get_vertiefungen_for
import pandas as pd

# === Lade Excel-Regeln ===
try:
    RULES = load_excel_rules("zulassung.xlsx")
except Exception as e:
    print(f"[WARN] Excel-Regeln konnten nicht geladen werden: {e}")
    RULES = {"Studiengänge": {}, "Allgemein": {}}


# === Fragenlogik ===
questions = [
    {"key": "abschlussziel", "text": "Für welchen Abschluss interessierst du dich?", "options": ["Bachelor", "Master"]},
    {"key": "hochschulzugang", "text": "Besitzt du eine Hochschulzugangsberechtigung (z. B. Abitur, Fachabitur oder eine berufliche Qualifikation)?", "options": ["Ja", "Nein"], "depends_on": {"abschlussziel": "Bachelor"}},
    {"key": "hsbi_bachelor", "text": "Hast du deinen Bachelor an der HSBI gemacht?", "options": ["Ja", "Nein"], "depends_on": {"abschlussziel": "Master"}},
    {"key": "bachelorstudiengang", "text": "Welchen Bachelorstudiengang hast du an der HSBI abgeschlossen?", "depends_on": {"hsbi_bachelor": "Ja"}},
    {"key": "studienart", "text": "Hast du praxisintegriert oder in Vollzeit studiert?", "options": ["praxisintegriert", "Vollzeit"], "depends_on": {"hsbi_bachelor": "Ja"}},
    {"key": "bachelorstudiengang", "text": "Welchen Studiengang hast du abgeschlossen?", "depends_on": {"hsbi_bachelor": "Nein"}},
    {"key": "studiengang", "text": "Für welchen Masterstudiengang interessierst du dich?", "options": ["Angewandte Automatisierung", "Digitale Technologien", "Maschinenbau", "Wirtschaftsingenieurwesen"], "depends_on": {"abschlussziel": "Master"}},
    {"key": "abschlussnote", "text": "Welche Abschlussnote hast du in deinem Vorstudium?", "depends_on": {"abschlussziel": "Master"}},
    {"key": "berufserfahrung", "text": "Wie viele Jahre Berufserfahrung hast du nach deinem Vorstudium gesammelt?", "depends_on": {"abschlussziel": "Master"}},
    {"key": "englischkenntnisse", "text": "Besitzt du Englischkenntnisse auf mindestens B2-Niveau?", "options": ["Ja", "Nein"], "depends_on": {"abschlussziel": "Master"}}
]


# === Funktion zur nächsten Frage ===
def get_next_question(state):
    """Bestimmt dynamisch die nächste Frage."""

    # 🧩 Falls gerade eine Vertiefung abgeschlossen wurde → Flag löschen
    if state.get("_vertiefung_done"):
        print("[INFO] Vertiefung abgeschlossen – nächste Frage wird bestimmt.")
        state["_vertiefung_done"] = False

    # 1️⃣ Abschlussziel fehlt → zuerst fragen
    if "abschlussziel" not in state:
        return {"key": "abschlussziel", "text": "Für welchen Abschluss interessierst du dich?", "options": ["Bachelor", "Master"]}

    # 2️⃣ Wenn Bachelor → HZB prüfen
    if state["abschlussziel"].lower() == "bachelor" and "hochschulzugang" not in state:
        return {
            "key": "hochschulzugang",
            "text": "Besitzt du eine Hochschulzugangsberechtigung (z. B. Abitur, Fachabitur oder eine berufliche Qualifikation)?",
            "options": ["Ja", "Nein"]
        }

    # 3️⃣ Wenn Masterbewerbung → ggf. Vertiefung abfragen
    if (
        state.get("abschlussziel", "").lower() == "master"
        and state.get("hsbi_bachelor", "").lower() == "ja"
        and "bachelorstudiengang" in state
        and "studienart" in state
        and "vertiefung" not in state
    ):
        vertiefungen = get_vertiefungen_for(state["bachelorstudiengang"], state["studienart"])
        if vertiefungen:
            print(f"🎯 Vertiefungsfrage wird gestellt: {vertiefungen}")
            return {
                "key": "vertiefung",
                "text": f"Welche Vertiefung hattest du in deinem Bachelorstudium ({state['bachelorstudiengang']})?",
                "options": vertiefungen
            }

    # 4️⃣ Sonst: nächste unbeantwortete Frage
    for q in questions:
        if "depends_on" in q:
            key, val = list(q["depends_on"].items())[0]
            if str(state.get(key, "")).lower() != str(val).lower():
                continue

        if q["key"] not in state:
            return q

    return None


# === Funktion zum Aktualisieren des Zustands ===
def update_state(state, user_input):
    """Aktualisiert den Gesprächszustand basierend auf der Nutzereingabe."""

    if user_input.lower() in ["ok", "weiter", "next"]:
        return {"state": state}

    # 🧩 Vertiefungsauswahl erkennen
    if "vertiefung" not in state and all(k in state for k in ["bachelorstudiengang", "studienart"]):
        vertiefungen = get_vertiefungen_for(state["bachelorstudiengang"], state["studienart"])
        if user_input in vertiefungen:
            state["vertiefung"] = user_input
            state["_vertiefung_done"] = True
            print(f"[STATE-UPDATE] Vertiefung gesetzt: {user_input}")

            # ECTS-Berechnung
            try:
                ects_data = calculate_bachelor_ects(state["bachelorstudiengang"], state["studienart"], user_input)
                if ects_data:
                    state["ects_ist"] = ects_data
                    print(f"[ECTS-Berechnung erfolgreich]: {ects_data}")
            except Exception as e:
                print(f"[Fehler bei ECTS-Berechnung]: {e}")

            return {"state": state}

    # 🔹 Normale Fragenabarbeitung
    for q in questions:
        if "depends_on" in q:
            key, val = list(q["depends_on"].items())[0]
            if str(state.get(key, "")).lower() != str(val).lower():
                continue
        if q["key"] not in state:
            state[q["key"]] = user_input
            return {"state": state}

    return {"state": state}
