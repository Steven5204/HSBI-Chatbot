from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
from openai_client import ask_openai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("rules.json", "r", encoding="utf-8") as f:
    RULES = json.load(f)

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message")

    rules_text = json.dumps(RULES, ensure_ascii=False, indent=2)
    prompt = f"""Die folgenden Daten beschreiben Zugangsvoraussetzungen für Masterstudiengänge:
    {rules_text}

    Analysiere diese Nutzerangabe:
    "{user_input}"

    Erkläre, ob die Person die Voraussetzungen erfüllt, und liste ggf. fehlende Unterlagen auf.
    """

    answer = ask_openai(prompt)
    return {"response": answer}
