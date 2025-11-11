import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_openai(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Du bist ein Studienberater der Hochschule. Antworte sachlich, freundlich und klar."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
