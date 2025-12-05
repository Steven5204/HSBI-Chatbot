from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from conversation import get_next_question, update_state, questions
from openai_client import get_openai_decision
from rules_excel import load_excel_rules



import uuid

# === App-Setup ===
app = FastAPI()
RULES = load_excel_rules()
SESSIONS = {}

# === CORS für Frontend erlauben ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Fortschritt berechnen ===
def calculate_progress(state: dict) -> int:
    """Berechnet Fortschritt in Prozent anhand der beantworteten Fragen."""
    total_questions = len(questions)
    answered = len([key for key in state.keys() if state[key]])
    if total_questions == 0:
        return 0
    progress = int((answered / total_questions) * 100)
    return min(progress, 100)

# === Chat-Route ===
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message", "").strip()
    user_id = data.get("user_id", str(uuid.uuid4()))

    # Lade Session-Zustand oder erzeuge neuen
    state = SESSIONS.get(user_id, {})

    # === Sicherstellen, dass state ein dict ist ===
    if not isinstance(state, dict):
        state = {}

    # === Update State ===
    state = update_state(state, message)
    SESSIONS[user_id] = state

    # === Nächste Frage bestimmen ===
    next_q = get_next_question(state)

    # === Falls noch Fragen offen sind ===
    if next_q:
        response_text = next_q["text"]
        options = next_q.get("options", [])
        progress = calculate_progress(state)

        return {
            "response": response_text,
            "options": options,
            "progress": progress
        }

    # === Wenn alle Fragen beantwortet sind → GPT Entscheidung ===
    try:
        decision_data = get_openai_decision(state, RULES)
        return {
            "response": decision_data["formatted_response"],
            "options": [],
            "progress": 100
        }
    except Exception as e:
        return {
            "response": f"❌ Fehler bei der Entscheidungsanalyse: {e}",
            "options": [],
            "progress": 100
        }

# === Startseite-Test ===
@app.get("/")
def root():
    return {"message": "HSBI Chatbot Backend läuft ✅"}

