def evaluate_bachelor(applicant):
    """
    Bewertet die Zugangsvoraussetzungen für Bachelorinteressierte.
    Es wird NUR die Hochschulzugangsberechtigung geprüft.
    """

    hz = applicant.get("hochschulzugang")

    if hz is None:
        return ("Unklar", "Ihre Hochschulzugangsberechtigung wurde nicht angegeben.")

    # 1) Volle Zugangsberechtigung
    if hz == "Allgemeine Hochschulreife":
        return ("Ja", "Sie erfüllen die Voraussetzungen für ein Bachelorstudium an der HSBI.")

    # 2) FH-Reife → Ja
    if hz == "Fachhochschulreife":
        return ("Ja", "Sie erfüllen die Voraussetzungen für ein Bachelorstudium an einer Fachhochschule.")

    # 3) Fachgebunden
    if hz == "Fachgebundene Hochschulreife":
        return (
            "Ja",
            "Mit Ihrer fachgebundenen Hochschulreife erfüllen Sie grundsätzlich die Voraussetzungen, "
            "sofern Ihr Fachbereich dem gewünschten Studiengang entspricht."
        )

    # 4) berufliche Qualifizierung → Ja, aber Hinweis
    if hz == "Berufliche Qualifizierung":
        return (
            "Ja",
            "Sie erfüllen die Voraussetzungen über eine berufliche Qualifizierung. "
            "Bitte beachten Sie, dass ggf. weitere Nachweise erforderlich sind."
        )

    # 5) ausländische HZB → unklar
    if hz == "Ausländische Hochschulzugangsberechtigung":
        return (
            "Unklar",
            "Ausländische Hochschulzugangsberechtigungen müssen individuell geprüft werden. "
            "Bitte wenden Sie sich an den Studienservice des Fachbereichs 3."
        )

    # Default fallback
    return ("Unklar", "Ihre Hochschulzugangsberechtigung konnte nicht eindeutig bewertet werden.")

def evaluate_master_intern(applicant, general_rules):
    """
    Bewertet die Zugangsvoraussetzungen für Masterbewerber*innen, die ihren Bachelor an der HSBI gemacht haben.
    ECTS-Fachlogik entfällt. Nur formale Kriterien werden geprüft.
    """

    issues = []

    # Note
    if "abschlussnote" not in applicant:
        issues.append("Keine Abschlussnote angegeben.")
    else:
        if float(applicant["abschlussnote"]) > float(general_rules["Mindestnote_Bachelor"]):
            issues.append("Ihre Abschlussnote erfüllt nicht die Mindestanforderung.")

    # Berufserfahrung
    if "berufserfahrung_jahre" not in applicant:
        issues.append("Berufserfahrung nicht angegeben.")
    else:
        if int(applicant["berufserfahrung_jahre"]) < int(general_rules["Berufserfahrung_Jahre"]):
            issues.append("Zu wenig Berufserfahrung.")

    # Englisch
    engl_map = {"Sehr gut": 1, "Gut": 2, "Befriedigend": 3, "Ausreichend": 4, "Mangelhaft": 5}
    user_engl = engl_map.get(applicant.get("englischkenntnisse"))
    req_engl = int(general_rules.get("Technisches_Englisch", 3))

    if user_engl is None:
        issues.append("Keine Angabe zu Englischkenntnissen.")
    elif user_engl > req_engl:
        issues.append("Ihre Englischkenntnisse erfüllen nicht die Mindestanforderung.")

    if not issues:
        return ("Ja", "Sie erfüllen die Voraussetzungen für den Masterstudiengang.")
    
    # Wenn wenige Fehler → unklar
    if len(issues) <= 2:
        return ("Unklar", "Einige Angaben erfüllen die Anforderungen nicht vollständig:\n- " + "\n- ".join(issues))

    # Viele Fehler → Ablehnung
    return ("Nein", "Sie erfüllen die Voraussetzungen leider nicht:\n- " + "\n- ".join(issues))


def evaluate_master_extern(applicant, program_rules, general_rules):
    """
    Bewertet externe Masterbewerber bzgl. fachlicher und formaler Anforderungen.
    """
    issues = []

    # 1) Formale Kriterien (Note, Berufserfahrung, Englisch)
    # wir wiederverwenden genau die Checks aus evaluate_master_intern:
    formal_check = evaluate_master_intern(applicant, general_rules)
    formal_status, formal_text = formal_check

    # Wenn formale Kriterien sehr schlecht → sofort ablehnen
    if formal_status == "Nein":
        return ("Nein", "Formale Kriterien nicht erfüllt:\n" + formal_text)

    # 2) Fachliche ECTS Prüfung
    ects_user = applicant.get("ects", {})  # TODO später: reales Mapping der Module

    ects_issues = []
    for category, needed in program_rules.items():
        if ects_user.get(category, 0) < needed:
            ects_issues.append(f"Zu wenige ECTS in {category} (mind. {needed})")

    # keine ECTS geprüft → user hat noch nichts angegeben → unklar
    if ects_user == {}:
        return ("Unklar", "Es wurden keine ECTS-Angaben gemacht. Bitte wenden Sie sich an den Studienservice.")

    # KEINE issues → bestehen
    if not ects_issues and formal_status == "Ja":
        return ("Ja", "Sie erfüllen sowohl die formalen als auch die fachlichen Voraussetzungen.")

    # wenige issues → unklar
    if len(ects_issues) <= 2:
        return ("Unklar", "Einige fachliche Anforderungen sind nicht eindeutig erfüllt:\n- " + "\n- ".join(ects_issues))

    # viele issues → eindeutige Ablehnung
    return ("Nein", "Sie erfüllen die fachlichen Voraussetzungen nicht:\n- " + "\n- ".join(ects_issues))

def match_general(applicant, general_rules):
    results = []

    # 1) Note
    if "abschlussnote" in applicant:
        if float(applicant.get("abschlussnote")) > float(general_rules["Mindestnote_Bachelor"]):
            results.append("Note schlechter als Minimalnote")
    else:
        results.append("Keine Abschlussnote angegeben")

    # 2) Berufserfahrung
    if "berufserfahrung_jahre" in applicant:
        if int(applicant.get("berufserfahrung_jahre")) < int(general_rules["Berufserfahrung_Jahre"]):
            results.append("Zu wenig Berufserfahrung")
    else:
        results.append("Keine Berufserfahrung angegeben")

    # 3) Englisch
    engl_map = {
        "Sehr gut": 1,
        "Gut": 2,
        "Befriedigend": 3,
        "Ausreichend": 4,
        "Mangelhaft": 5
    }

    user_level = applicant.get("englischkenntnisse")
    required_level = general_rules.get("Technisches_Englisch")

    # Falls der Nutzer noch nichts angegeben hat
    if user_level is None:
        results.append("Englischniveau fehlt")
        return results

    # user-level convertieren
    user_score = engl_map.get(user_level)
    if user_score is None:
        results.append("Englischniveau ungültig")
        return results

    # required_level ist evtl. eine Zahl (z.B. 3)
    if isinstance(required_level, (int, float)):
        req_score = int(required_level)
    else:
        req_score = engl_map.get(required_level, 3)

    # jetzt sicher vergleichen
    if user_score > req_score:
        results.append("Englischniveau nicht ausreichend")

    return results

def match_program(applicant, program_rules):
    results = []
    ects_user = applicant.get("ects", {})

    for category, needed in program_rules.items():
        if ects_user.get(category, 0) < needed:
            results.append(f"Zu wenige ECTS in Kategorie {category}")

    return results

def final_decision(gen_issues, prog_issues):
    if not gen_issues and not prog_issues:
        return "Ja", "Alle Voraussetzungen sind erfüllt."

    if len(gen_issues) + len(prog_issues) > 3:
        return "Nein", "Mehrere Voraussetzungen fehlen:\n- " + "\n- ".join(gen_issues + prog_issues)

    return "Unklar", "Bitte Studienservice kontaktieren."
