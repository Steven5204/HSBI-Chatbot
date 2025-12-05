def evaluate_bachelor(applicant):
    hz = applicant.get("hochschulzugang")
    if hz is None:
        return ("Unklar", "Keine Hochschulzugangsberechtigung angegeben.")
    mapping = {
        "Allgemeine Hochschulreife": "Sie erfüllen die Voraussetzungen für ein Bachelorstudium.",
        "Fachhochschulreife": "Sie erfüllen die Voraussetzungen für ein FH-Bachelorstudium.",
        "Fachgebundene Hochschulreife": "Sie erfüllen grundsätzlich die Voraussetzungen, sofern Ihr Fachbereich passt.",
        "Berufliche Qualifizierung": "Sie erfüllen die Voraussetzungen über berufliche Qualifikation.",
        "Ausländische Hochschulzugangsberechtigung": "Bitte wenden Sie sich an den Studienservice – individuelle Prüfung erforderlich."
    }
    return ("Ja" if hz != "Ausländische Hochschulzugangsberechtigung" else "Unklar", mapping.get(hz, "Unbekannte HZB."))

def evaluate_master_intern(applicant, rules):
    """Prüft interne Bewerber (HSBI) dynamisch anhand der Excel-Regeln."""
    general = rules.get("Allgemein", {})
    studies = rules.get("Studiengänge", {})

    issues = []
    bachelor = applicant.get("bachelor_hsbi")
    target = applicant.get("studiengang")

    # === Allgemeine Anforderungen dynamisch prüfen ===
    try:
        note = float(applicant.get("abschlussnote", 5))
        min_note = float(general.get("Mindestnote_Bachelor", 2.5))
        if note > min_note:
            issues.append(f"Abschlussnote ({note}) liegt über dem Grenzwert ({min_note}).")
    except Exception:
        issues.append("Ungültige Abschlussnote.")

    try:
        erf = int(applicant.get("berufserfahrung_jahre", 0))
        min_erf = int(general.get("Berufserfahrung_Jahre", 1))
        if erf < min_erf:
            issues.append(f"Nur {erf} Jahre Berufserfahrung (erforderlich: {min_erf}).")
    except Exception:
        issues.append("Ungültige Berufserfahrung.")

    engl_map = {"Sehr gut": 1, "Gut": 2, "Befriedigend": 3, "Ausreichend": 4, "Mangelhaft": 5}
    user_lvl = engl_map.get(applicant.get("englischkenntnisse"))
    req_lvl = int(general.get("Technisches_Englisch", 3))
    if user_lvl and user_lvl > req_lvl:
        issues.append("Englischniveau nicht ausreichend.")

    # === Modulvergleich Bachelor → Ziel-Master ===
    if bachelor in studies and target in studies:
        src_mods = studies[bachelor]["ECTS_Anforderungen"]
        trg_mods = studies[target]["ECTS_Anforderungen"]

        for fach, needed in trg_mods.items():
            have = src_mods.get(fach, 0)
            if have < needed:
                issues.append(f"Zu wenige ECTS in {fach} (haben {have}, benötigt {needed}).")

    # === Entscheidung ableiten ===
    if not issues:
        return ("Ja", "Alle formalen und fachlichen Kriterien erfüllt.")
    elif len(issues) <= 2:
        return ("Unklar", "Teilweise Abweichungen:\n- " + "\n- ".join(issues))
    else:
        return ("Nein", "Voraussetzungen nicht erfüllt:\n- " + "\n- ".join(issues))

def evaluate_master_extern(applicant, rules):
    """Prüft externe Bewerber anhand der Excel-Regeln (ohne Modulvergleich)."""
    general = rules.get("Allgemein", {})
    studies = rules.get("Studiengänge", {})
    target = applicant.get("studiengang")

    issues = []

    # === Allgemeine Regeln wie oben ===
    try:
        note = float(applicant.get("abschlussnote", 5))
        min_note = float(general.get("Mindestnote_Bachelor", 2.5))
        if note > min_note:
            issues.append(f"Abschlussnote ({note}) liegt über dem Grenzwert ({min_note}).")
    except Exception:
        issues.append("Ungültige Abschlussnote.")

    try:
        erf = int(applicant.get("berufserfahrung_jahre", 0))
        min_erf = int(general.get("Berufserfahrung_Jahre", 1))
        if erf < min_erf:
            issues.append(f"Nur {erf} Jahre Berufserfahrung (erforderlich: {min_erf}).")
    except Exception:
        issues.append("Ungültige Berufserfahrung.")

    # === ECTS-Minimum (aus Zielstudiengangsanforderungen) ===
    if target in studies:
        trg_mods = studies[target]["ECTS_Anforderungen"]
        for fach, needed in trg_mods.items():
            # externe geben keine Modulverteilung an → nur deklarativen Hinweis
            issues.append(f"Nachweis von mindestens {needed} ECTS in {fach} erforderlich (Prüfung durch Prüfungsamt).")

    if not issues:
        return ("Ja", "Alle formalen Voraussetzungen erfüllt. Endgültige Prüfung durch Prüfungsamt.")
    else:
        return ("Unklar", "Erforderliche Unterlagen und Nachweise werden geprüft:\n- " + "\n- ".join(issues))