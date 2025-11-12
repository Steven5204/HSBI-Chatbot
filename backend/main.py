from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai_client import ask_openai
from conversation import get_next_question, update_state, summarize_answers

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Zwischenspeicher für Sitzungsdaten (einfach für MVP)
SESSIONS = {}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_id = data.get("user_id", "default")
    user_input = data.get("message")

    # Initialer Zustand pro Nutzer
    if user_id not in SESSIONS:
        SESSIONS[user_id] = {"current_index": 0}
        welcome_message = (
            "🎓 Willkommen beim Studienberater-Chatbot!\n\n"
            "Ich helfe Ihnen herauszufinden, ob Sie die Zulassungsvoraussetzungen "
            "für den Master erfüllen.\n\n"
            "Bitte beantworten Sie mir ein paar kurze Fragen. "
            "Tippen Sie 'Start', um zu beginnen."
        )
        return {"response": welcome_message, "progress": 0}

    # Aktuelle Sitzung abrufen
    state = SESSIONS[user_id]

    # Benutzer antwortet -> speichern
    if user_input.lower() != "start":
        state = update_state(state, user_input)
        SESSIONS[user_id] = state

    # Nächste Frage bestimmen
    next_question = get_next_question(state)

    if next_question:
        progress = int((state["current_index"] / 5) * 100)
        return {"response": next_question, "progress": progress}
    else:
        # Alle Fragen beantwortet → Zusammenfassung + KI-Bewertung
        summary = summarize_answers(state)
        prompt = f"""
        Hier sind die Angaben eines Studieninteressierten:

        {summary}

        Prüfe anhand der dir bekannten Zulassungsvoraussetzungen für Masterstudiengänge
        und gib eine klare Entscheidung:
        - Ob die Voraussetzungen erfüllt sind
        - Falls nicht: welche Punkte fehlen
        """

        decision = ask_openai(prompt)
        SESSIONS.pop(user_id, None)  # Sitzung zurücksetzen
        return {"response": decision, "progress": 100}
