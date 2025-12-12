from openai import OpenAI
import os
import json
import re
import difflib
from dotenv import load_dotenv
import re
from rules_excel import calculate_bachelor_ects
import pandas as pd


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def format_markdown_response(raw_text: str) -> str:
    """
    Formatiert eine von GPT generierte Markdown-Antwort in HTML,
    damit sie im Chat sauber dargestellt wird.
    """
    if not raw_text:
        return "Keine Entscheidung verfügbar."

    text = raw_text.strip()

    # Ersetze spezielle Bereiche mit Icons und HTML-Struktur
    replacements = {
        r"- \*\*Entscheidung:\*\*": " <b>Entscheidung:</b>",
        r"- \*\*Begründung:\*\*": " <b>Begründung:</b>",
        r"- \*\*ECTS-Vergleich:\*\*": " <b>ECTS-Vergleich:</b>",
        r"- \*\*Bewertung:\*\*": " <b>Bewertung:</b>",
        r"- \*\*Weitere Voraussetzungen:\*\*": " <b>Weitere Voraussetzungen:</b>",
        r"- \*\*Bewerbungsunterlagen:\*\*": " <b>Bewerbungsunterlagen:</b>",
        r"- \*\*Soll:\*\*": "<u>Soll:</u>",
        r"- \*\*Ist:\*\*": "<u>Ist:</u>",
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    # Normale Listenpunkte hübsch einrücken
    text = re.sub(r"^- ", "• ", text, flags=re.MULTILINE)

    # Zeilenumbrüche in <br> umwandeln
    text = text.replace("\n", "<br>")

    # Schönes Box-Layout für Chat
    formatted = f"""
    <div style='background-color:#f1f6ff;padding:12px;border-radius:10px;line-height:1.6;font-size:15px;'>
        {text}
    </div>
    """

    return formatted


# 🧮 Vergleich Soll vs. Ist → Regelbasierte Entscheidung
def evaluate_ects_decision(ects_soll, ects_ist):
    """
    Vergleicht Soll- und Ist-ECTS und liefert:
    - "Ja" wenn alle Anforderungen erfüllt oder übertroffen sind
    - "Unklar" wenn bis zu 10 ECTS fehlen
    - "Nein" wenn mehr als 10 ECTS fehlen
    Gibt zusätzlich eine Textbeschreibung des Vergleichs zurück.
    """
    if not ects_ist or not ects_soll:
        return (
            "Unklar",
            "Einzelfallprüfung nötig, da unvollständige ECTS-Daten vorliegen.",
            "Keine ausreichenden Vergleichsdaten verfügbar."
        )

    # 🔹 Einheitliche Keys (klein schreiben)
    ects_soll = {k.strip().lower(): float(v) for k, v in ects_soll.items() if v is not None}
    ects_ist = {k.strip().lower(): float(v) for k, v in ects_ist.items() if v is not None}

    fehlende_gesamt = 0
    details = []
    vergleich_zeilen = []

    for k, soll in ects_soll.items():
        ist = ects_ist.get(k, 0.0)
        diff = round(soll - ist, 2)

        if ist < soll:
            fehlende_gesamt += diff
            vergleich_zeilen.append(f"• {k.capitalize()}: Soll {soll} / Ist {ist} → {diff} ECTS zu wenig")
        else:
            vergleich_zeilen.append(f"• {k.capitalize()}: Soll {soll} / Ist {ist} → erfüllt")

    # 🔹 Bewertung nach fehlenden Punkten
    if fehlende_gesamt == 0:
        auto_decision = "Ja"
        auto_reason = "Alle ECTS-Anforderungen sind erfüllt oder übertroffen."
    elif fehlende_gesamt <= 10:
        auto_decision = "Unklar"
        auto_reason = (
            f"Insgesamt fehlen nur {fehlende_gesamt} ECTS, insbesondere im Bereich "
            f"{', '.join([k.capitalize() for k, soll in ects_soll.items() if ects_ist.get(k, 0) < soll])}. "
            "Dies stellt einen Grenzfall dar und könnte im Einzelfall akzeptabel sein. "
            "Daher wird eine Bewerbung empfohlen."
        )
    else:
        auto_decision = "Nein"
        auto_reason = (
            f"Es fehlen insgesamt {fehlende_gesamt} ECTS in den Bereichen "
            f"{', '.join([k.capitalize() for k, soll in ects_soll.items() if ects_ist.get(k, 0) < soll])}. "
            "Die Voraussetzungen sind aktuell nicht erfüllt."
        )

    ects_comparison_text = "\n".join(vergleich_zeilen)

    return auto_decision, auto_reason, ects_comparison_text

def get_openai_decision(applicant_data: dict, rules: dict):
    """
    Übergibt die gesammelten Bewerberdaten und Studienregeln an OpenAI,
    um automatisch zu prüfen, ob die Voraussetzungen erfüllt sind.
    Für Bachelorbewerber: nur HZB-Prüfung.
    Für Masterbewerber: vollständige ECTS- und Regelprüfung.
    """
    try:
        # 🔹 Sicherstellen, dass applicant_data ein dict ist
        if not isinstance(applicant_data, dict):
            applicant_data = {}

        # 🔹 Nutzerkategorie automatisch bestimmen
        hsbi_status = (applicant_data.get("hsbi_bachelor") or "").strip().lower()
        nutzerkategorie = "intern" if hsbi_status == "ja" else "extern"

        # 🔹 Abschlussziel, HZB und Studiengänge extrahieren
        abschlussziel = (applicant_data.get("abschlussziel") or "").strip().lower()
        hochschulzugang = (applicant_data.get("hochschulzugang") or "").strip().lower()
        bachelorstudiengang = applicant_data.get("bachelorstudiengang", "Unbekannt")
        masterstudiengang = applicant_data.get("studiengang", "Unbekannt")

        # 🔹 GPT System Prompt
        system_prompt = """
        Du bist Bifi, der digitale Studienberater der Hochschule Bielefeld (HSBI).
        Sprich den Nutzer stets direkt mit „du“ oder „deine“ an – nicht in der dritten Person.
        Analysiere die Bewerberdaten und prüfe anhand der gegebenen Informationen, 
        ob die Zulassungsvoraussetzungen erfüllt sind.
        Formuliere klar, freundlich und verständlich im Markdown-Format, **ohne Emojis oder Symbole**.

        Das Format deiner Antwort:
        - **Entscheidung:** Ja / Nein / Unklar
        - **Begründung:** Warum oder warum nicht
        - **ECTS-Vergleich:** Falls relevant, liste Soll/Ist im direkten Vergelich und Bewertung auf
        - **Weitere Voraussetzungen:** Note, Berufserfahrung, Englischkenntnisse
        - **Bewerbungsunterlagen:** Welche Unterlagen du einreichen musst
        """

        # 🔹 Unterschiedliche Logik: Bachelor vs Master
        if "bachelor" in abschlussziel:
            if hochschulzugang == "ja":
                formatted_output = format_markdown_response("""
                - **Entscheidung:** Ja  
                - **Begründung:** Der Bewerber besitzt eine anerkannte Hochschulzugangsberechtigung (z. B. Abitur, Fachabitur oder berufliche Qualifikation) und erfüllt damit die formalen Voraussetzungen für ein Bachelorstudium an der HSBI.  
                - **Bewerbungsunterlagen:** Abschlusszeugnis, Lebenslauf, ggf. Nachweis über berufliche Qualifikation.
                """)
                return {"formatted_response": formatted_output}

            elif hochschulzugang == "nein":
                formatted_output = format_markdown_response("""
                - **Entscheidung:** Nein  
                - **Begründung:** Es liegt keine Hochschulzugangsberechtigung vor. Eine Zulassung zum Bachelorstudium ist daher nicht möglich.  
                - **Bewerbungsunterlagen:** Keine – bitte wenden Sie sich an die Studienberatung für alternative Zugangswege.
                """)
                return {"formatted_response": formatted_output}
            
            # 🟦 Bachelorbewerber → Nur HZB-Prüfung
            user_prompt = f"""
            Der Bewerber möchte einen Bachelorstudiengang beginnen.
            Prüfe, ob eine Hochschulzugangsberechtigung (z. B. Abitur, Fachabitur, berufliche Qualifikation) vorliegt.

            Bewerberdaten:
            {json.dumps(applicant_data, indent=2, ensure_ascii=False)}

            Antworte klar im Markdown-Format:
            - **Entscheidung:** Ja/Nein
            - **Begründung:** Warum oder warum nicht
            - **Weitere Voraussetzungen:** ggf. ergänzende Anforderungen (z. B. Sprachkenntnisse)
            - **Bewerbungsunterlagen:** Welche Dokumente müssen eingereicht werden (z. B. Zeugnisse, Lebenslauf)
            """
        else:
            # 🟨 Masterbewerber → Extern vs Intern unterscheiden
            if nutzerkategorie == "extern":
                user_prompt = f"""
                Du bist Bifi, der Studienberater der HSBI.
                Der Bewerber ist interner Masterbewerber.

                Hier sind die bereits automatisch ausgewerteten Ergebnisse aus der Excel-Datenbasis:

                Automatische Entscheidung: {auto_decision}
                Automatische Begründung: {auto_reason}

                Bewerberdaten:
                {json.dumps(applicant_data, indent=2, ensure_ascii=False)}

                ECTS-Vergleich laut Excel-Daten:

                Soll:
                {ects_soll_text}

                Ist (berechnet aus Bachelor-Struktur):
                {ects_ist_text}

                Analysiere die Ergebnisse. Verwende die automatische Entscheidung und Begründung als Grundlage.
                Formuliere sie im freundlichen, klaren Markdown-Stil.

                Antworte im Markdown-Format:
                - **Entscheidung:** Ja/Nein/Unklar
                - **Begründung:** Warum oder warum nicht
                - **ECTS-Vergleich:** Liste Soll/Ist und Bewertung auf
                - **Weitere Voraussetzungen:** Note, Berufserfahrung, Englischkenntnisse
                - **Bewerbungsunterlagen:** Welche Unterlagen erforderlich sind
                """
            else:
                # 🟩 INTERNER MASTERBEWERBER MIT ECHTEM ECTS-VERGLEICH ------------------
                
                # 🆕 1️⃣ Excel-Daten laden
                df_zusammensetzung = pd.read_excel("zulassung.xlsx", sheet_name="Modulzusammensetzung")
                df_modules = pd.read_excel("zulassung.xlsx", sheet_name="Module")

                # 🆕 2️⃣ ECTS berechnen (Ist-Werte)
                ects_ist = calculate_bachelor_ects(
                    bachelorstudiengang,
                    applicant_data.get("studienart", ""),
                    applicant_data.get("vertiefung", ""),
                )

                
                # 🆕 3️⃣ Soll-Werte aus Rules extrahieren
                ects_soll = {}
                if "Studiengänge" in rules and masterstudiengang in rules["Studiengänge"]:
                    ects_soll = rules["Studiengänge"][masterstudiengang].get("ECTS_Anforderungen", {})

                # 🧮 Automatische Entscheidung basierend auf Soll-/Ist-ECTS
                auto_decision, auto_reason, ects_comparison_text = evaluate_ects_decision(ects_soll, ects_ist)


                # 🆕 4️⃣ ECTS schön formatieren
                ects_ist_text = (
                    "\n".join([f"- {k}: {v} ECTS" for k, v in ects_ist.items()])
                    if ects_ist else "- Keine Daten verfügbar"
                )
                ects_soll_text = (
                    "\n".join([f"- {k}: {v} ECTS" for k, v in ects_soll.items()])
                    if ects_soll else "- Keine Angaben verfügbar"
                )

                # 🆕 5️⃣ Prompt vorbereiten
                user_prompt = f"""
                Du bist Bifi, der digitale Studienberater der Hochschule Bielefeld (HSBI).
                Der Bewerber ist interner Masterbewerber.

                Deine Aufgabe:
                🟩 Verwende ausschließlich die automatisch berechnete Entscheidung und Begründung unten.
                🟥 Ändere sie nicht und rechne NICHT selbst mit den ECTS-Werten.

                ---

                📊 **Automatische Bewertung:**
                - Entscheidung: **{auto_decision}**
                - Begründung: **{auto_reason}**

                ---

                📘 **ECTS-Vergleich laut Excel-Daten:**

                **Soll-Werte:**
                {ects_soll_text}

                **Ist-Werte (berechnet aus Bachelor-Struktur):**
                {ects_ist_text}

                **Direkter Vergleich:**
                {ects_comparison_text}

                ---

                📋 **Bewerberdaten:**
                {json.dumps(applicant_data, indent=2, ensure_ascii=False)}

                ---

                🧠 **Deine Aufgabe:**
                Formuliere die endgültige Rückmeldung an den Bewerber basierend auf diesen Daten.
                Verwende ausschließlich die automatische Entscheidung und Begründung oben und schreibe
                eine klare, freundliche und professionelle Antwort im Markdown-Format.

                Das Format muss exakt so aussehen:

                - **Entscheidung:** {auto_decision}
                - **Begründung:** Formuliere die automatische Begründung flüssig und verständlich.
                - **ECTS-Vergleich:** Gib den direkten Vergleich aus ({ects_comparison_text}) und erkläre kurz, was das bedeutet.
                - **Weitere Voraussetzungen:** Erwähne Note, Berufserfahrung und Englischkenntnisse aus den Bewerberdaten.
                - **Bewerbungsunterlagen:** Liste auf, welche Unterlagen der Bewerber einreichen sollte.

                ❗Wichtig:
                - Du darfst keine neuen ECTS-Werte berechnen.
                - Du darfst die Entscheidung nicht verändern.
                - Antworte ausschließlich im **Markdown-Format** ohne Emojis oder Symbole.
                """

        # 🔹 GPT-Aufruf
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )

        # 🔹 Antwort verarbeiten
        decision_text = ""
        if hasattr(response, "choices") and len(response.choices) > 0:
            decision_text = response.choices[0].message.content.strip()

        # 🔹 Entscheidung direkt aus dem GPT-Text extrahieren
        decision_match = re.search(r"Entscheidung:\s*(Ja|Nein|Unklar)", decision_text, re.IGNORECASE)
        decision_value = decision_match.group(1).capitalize() if decision_match else "Unklar"

        # 🔹 Formatieren oder Fallback
        if not decision_text:
            formatted_output = "⚠️ Keine Antwort vom Entscheidungsmodul erhalten."
            decision_value = "Unklar"
        else:
            formatted_output = format_markdown_response(decision_text)

            # 🔍 Entscheidung (Ja/Nein/Unklar) aus dem GPT-Text extrahieren
            match = re.search(r"(?i)\b(ja|nein|unklar)\b", decision_text)
            decision_value = match.group(1).capitalize() if match else "Unklar"

        # 🧩 Immer Entscheidung mitsenden
        return {
            "formatted_response": formatted_output,
            "decision": decision_value
        }

    except Exception as e:
        return {
            "formatted_response": f"❌ Fehler bei der Entscheidungsanalyse: {str(e)}",
            "decision": "Unklar"
        }
