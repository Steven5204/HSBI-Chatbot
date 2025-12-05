# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from rules_excel import load_excel_rules
from openai_client import get_openai_decision
from conversation import update_state, get_next_question, questions
from logging_handler import log_event
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# === CORS KONFIGURATION ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # oder: ["http://127.0.0.1:5500"] wenn du mit LiveServer arbeitest
    allow_credentials=True,
    allow_methods=["*"],          # <--- hier erlauben wir auch OPTIONS!
    allow_headers=["*"],
)

RULES = load_excel_rules("zulassung.xlsx")
SESSIONS = {}


class ChatRequest(BaseModel):
    user_id: str
    message: str


@app.post("/chat")
async def chat(request: ChatRequest):
    user_id = request.user_id
    user_input = request.message.strip()

    if user_id not in SESSIONS:
        SESSIONS[user_id] = {"state": {}, "progress": 0}
    state = SESSIONS[user_id]["state"]

    # Eingabe speichern
    state = update_state(state, user_input)

    # Nächste Frage finden
    next_question = get_next_question(state)

    if next_question:
        options = next_question.get("options")
        answered = len([k for k in state.keys() if k in [q["key"] for q in questions]])
        total = len([q for q in questions if "depends_on" not in q or all(state.get(k) == v for k, v in q["depends_on"].items())])
        progress = int((answered / total) * 100)
        SESSIONS[user_id]["progress"] = progress

        return {
            "response": next_question["text"],
            "options": options,
            "progress": progress
        }

    # Wenn keine weiteren Fragen mehr offen sind → OpenAI entscheidet
    decision_data = get_openai_decision(state, RULES)

    log_event({
        "user_id": user_id,
        "entscheidung": decision_data["entscheidung"],
        "studiengang": state.get("studiengang"),
        "nutzerkategorie": state.get("nutzerkategorie"),
        "completed": True
    })

    return {
        "response": decision_data["formatted_response"],
        "progress": 100,
        "options": None
    }
