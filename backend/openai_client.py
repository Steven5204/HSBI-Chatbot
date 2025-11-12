import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_openai(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Du bist ein Studienberater der Hochschule Bielefeld. Studierende fragen dich, ob Sie alle Zulassungsvoraussetzungen für ein bestimmtes Studium erfüllen. Stelle nacheinander Fragen, um alle nötigen Informationen einzuholen, die du brauchst. Fasse abschließend kurz zusammen, ob die Person alle Voraussetzungen erfüllt oder nicht."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
