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

def evaluate_master_intern(applicant, general_rules):
    issues = []
    try:
        note = float(applicant.get("abschlussnote", 5))
        if note > float(general_rules.get("Mindestnote_Bachelor", 2.5)):
            issues.append("Abschlussnote zu schlecht.")
    except ValueError:
        issues.append("Ungültige Note.")
    try:
        erf = int(applicant.get("berufserfahrung_jahre", 0))
        if erf < int(general_rules.get("Berufserfahrung_Jahre", 1)):
            issues.append("Zu wenig Berufserfahrung.")
    except ValueError:
        issues.append("Ungültige Berufserfahrung.")
    engl_map = {"Sehr gut": 1, "Gut": 2, "Befriedigend": 3, "Ausreichend": 4, "Mangelhaft": 5}
    user_lvl = engl_map.get(applicant.get("englischkenntnisse"))
    req_lvl = int(general_rules.get("Technisches_Englisch", 3))
    if user_lvl and user_lvl > req_lvl:
        issues.append("Englischniveau nicht ausreichend.")
    if not issues:
        return ("Ja", "Sie erfüllen die Voraussetzungen.")
    elif len(issues) <= 2:
        return ("Unklar", "Einige Angaben sind grenzwertig:\n- " + "\n- ".join(issues))
    else:
        return ("Nein", "Sie erfüllen die Voraussetzungen leider nicht:\n- " + "\n- ".join(issues))

def evaluate_master_extern(applicant, program_rules, general_rules):
    status, text = evaluate_master_intern(applicant, general_rules)
    if status == "Nein":
        return ("Nein", text)
    ects_user = applicant.get("ects", {})
    ects_issues = []
    for cat, needed in program_rules.items():
        if ects_user.get(cat, 0) < needed:
            ects_issues.append(f"Zu wenige ECTS in {cat} (min. {needed})")
    if not ects_issues and status == "Ja":
        return ("Ja", "Alle formalen und fachlichen Kriterien erfüllt.")
    elif len(ects_issues) <= 2:
        return ("Unklar", "Einige ECTS-Kriterien unklar:\n- " + "\n- ".join(ects_issues))
    else:
        return ("Nein", "Fachliche Kriterien nicht erfüllt:\n- " + "\n- ".join(ects_issues))
