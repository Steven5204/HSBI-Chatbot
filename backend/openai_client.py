from openai import OpenAI
import os
import json
import re
import difflib
from dotenv import load_dotenv
import re


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
                Du bist Studienberater der HSBI. Der Bewerber möchte sich extern für einen Masterstudiengang bewerben.

                Bewerberdaten:
                {json.dumps(applicant_data, indent=2, ensure_ascii=False)}

                Studienregeln (aus Excel):
                {json.dumps(rules, indent=2, ensure_ascii=False)}

                Erkläre, dass keine ECTS-Angaben geprüft werden können, 
                da diese erst durch das Prüfungsamt bewertet werden.
                Beurteile nur die formalen Voraussetzungen (Note, Berufserfahrung, Englischkenntnisse).
                Wenn diese vorliegen, gib aus, dass eine vorläufige Zulassung möglich ist, unter der Voraussetzunge, dass die abgeschlossenen Module ähnlich genug sind.
                

                Antworte im Markdown-Format:
                - **Entscheidung:** Ja/Nein/Unklar
                - **Begründung:** Warum oder warum nicht
                - **Weitere Voraussetzungen:** Note, Berufserfahrung, Englischkenntnisse
                - **Bewerbungsunterlagen:** Welche Unterlagen erforderlich sind
                """
            else:
                # 🟩 Interner Bewerber → mit ECTS-Vergleich
                # 🧮 ECTS-Daten aus conversation.py verwenden
                ects_ist = applicant_data.get("ects_ist", {})
                ects_soll = rules.get("ects_anforderungen", {})  # falls du Soll-ECTS aus Excel übergibst

                # 📊 ECTS in Textform bringen
                ects_ist_text = (
                    "\n".join([f"- {k}: {v} ECTS" for k, v in ects_ist.items()])
                    if ects_ist else "- Keine Daten verfügbar"
                )
                ects_soll_text = (
                    "\n".join([f"- {k}: {v} ECTS" for k, v in ects_soll.items()])
                    if ects_soll else "- Keine Angaben verfügbar"
                )
                user_prompt = f"""
                Du bist Studienberater der HSBI. Der Bewerber ist interner Masterbewerber.

                Bewerberdaten:
                {json.dumps(applicant_data, indent=2, ensure_ascii=False)}

                Studienregeln (aus Excel):
                {json.dumps(rules, indent=2, ensure_ascii=False)}

                **ECTS-Vergleich laut Excel-Daten:**

                Soll:
                {ects_soll_text}

                Ist (berechnet aus Bachelor-Struktur):
                {ects_ist_text}

                Analysiere die Voraussetzungen inkl. ECTS-Vergleich. 
                Zeige Soll/Ist und bewerte, ob die Anforderungen erfüllt sind.

                Antworte im Markdown-Format:
                - **Entscheidung:** Ja/Nein/Unklar
                - **Begründung:** Warum oder warum nicht
                - **ECTS-Vergleich:** Liste Soll/Ist und Bewertung auf
                - **Weitere Voraussetzungen:** Note, Berufserfahrung, Englischkenntnisse
                - **Bewerbungsunterlagen:** Welche Unterlagen erforderlich sind
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
