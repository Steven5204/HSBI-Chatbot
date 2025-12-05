from openai import OpenAI
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_openai_decision(applicant_data, rules):
    """
    GPT bewertet den Bewerber anhand der Excel-Daten.
    Gibt Entscheidung, Begründung, ECTS-Vergleich und Checkliste formatiert zurück.
    """
    prompt = f"""
    Du bist ein sachlicher, deutschsprachiger Studienberater der Hochschule Bielefeld (HSBI).
    Analysiere die Bewerberdaten und vergleiche sie mit dem Regelwerk aus der Excel-Datei.
    Antworte ausschließlich auf Deutsch.

    ### Bewerberdaten:
    {json.dumps(applicant_data, ensure_ascii=False, indent=2)}

    ### Regelwerk (aus Excel):
    {json.dumps(rules, ensure_ascii=False, indent=2)}

    ---
    **Aufgabe:**
    1. Vergleiche die vorhandenen ECTS-Leistungen des Bewerbers mit den geforderten Werten aus der Excel-Datei.
       - Zeige für jeden Fachbereich (z. B. Mathematik, Informatik, Technik etc.) den Soll- und Ist-Wert.
       - Bewerte jeden Punkt mit "✅ Erfüllt", "⚠️ Unklar" oder "❌ Nicht erfüllt".
    2. Gib zusätzlich an, welche allgemeinen Voraussetzungen erfüllt sind (Note, Berufserfahrung, Englischkenntnisse etc.).
    3. Erkläre kurz, ob die Person zugelassen werden kann ("Ja", "Nein", "Unklar").
    4. Gib am Ende eine Beschreibung der einzureichenden Bewerbungsunterlagen.
    5. Antworte ausschließlich im folgenden JSON-Format:

    {{
      "entscheidung": "Ja" | "Nein" | "Unklar",
      "begruendung": "string",
      "ects_vergleich": [
        {{
          "fachbereich": "string",
          "gefordert": number,
          "vorhanden": number,
          "bewertung": "✅ Erfüllt" | "⚠️ Unklar" | "❌ Nicht erfüllt"
        }}
      ],
      "weitere_voraussetzungen": [
        "string"
      ],
      "checkliste": "string"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein präziser, deutscher Studienberater der HSBI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )

        text = response.choices[0].message.content.strip()

        # 🔍 JSON erkennen und parsen
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            json_text = match.group(0)
            result = json.loads(json_text)
        else:
            result = {
                "entscheidung": "Unklar",
                "begruendung": text,
                "ects_vergleich": [],
                "weitere_voraussetzungen": [],
                "checkliste": "Keine formatierten Daten erkannt."
            }

        # 🔹 Formatierung des ECTS-Vergleichs
        ects_lines = []
        for e in result.get("ects_vergleich", []):
            ects_lines.append(
                f"{e['fachbereich']}: {e['vorhanden']} / {e['gefordert']} ECTS → {e['bewertung']}"
            )

        weitere_voraussetzungen = "\n".join(
            [f"✅ {v}" for v in result.get("weitere_voraussetzungen", [])]
        )

        formatted_response = (
            f"📋 **Entscheidung:** {result.get('entscheidung', 'Unklar')}\n\n"
            f"**Begründung:**\n{result.get('begruendung', '').strip()}\n\n"
            f"**📊 ECTS-Vergleich:**\n" +
            ("\n".join(ects_lines) if ects_lines else "– Keine Daten –") +
            "\n\n**Weitere Voraussetzungen:**\n" +
            (weitere_voraussetzungen or "– Keine Angaben –") +
            "\n\n**Bewerbungsunterlagen:**\n" +
            result.get("checkliste", "")
        )

        return {
            "entscheidung": result.get("entscheidung", "Unklar"),
            "begruendung": result.get("begruendung", ""),
            "ects_vergleich": result.get("ects_vergleich", []),
            "weitere_voraussetzungen": result.get("weitere_voraussetzungen", []),
            "checkliste": result.get("checkliste", ""),
            "formatted_response": formatted_response
        }

    except Exception as e:
        return {
            "entscheidung": "Fehler",
            "begruendung": f"API-Fehler: {e}",
            "ects_vergleich": [],
            "weitere_voraussetzungen": [],
            "checkliste": "Keine Entscheidung möglich.",
            "formatted_response": f"❌ Fehler bei der Entscheidung: {e}"
        }
