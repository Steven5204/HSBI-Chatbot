from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from conversation import (
    questions,
    update_state,
    get_next_question,
    get_ects_info,
    condition_met,
    count_relevant_questions,
    RULES
)
from matching import (
    evaluate_bachelor,
    evaluate_master_intern,
    evaluate_master_extern
)
from logging_handler import log_event

app = FastAPI(title="HSBI Chatbot Bifi")

# ✅ CORS erlauben für dein Frontend (egal ob Live Server oder lokal)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Session-Speicher
SESSIONS = {}

# ✅ Request-Struktur
class ChatRequest(BaseModel):
    message: str
    user_id: str


@app.post("/chat")
async def chat(request: ChatRequest):
    user_id = request.user_id
    user_input = request.message.strip()

    # Initialisiere Session
    if user_id not in SESSIONS:
        SESSIONS[user_id] = {"state": {}, "progress": 0}

    state = SESSIONS[user_id]["state"]

    # 1️⃣ Antwort speichern / Zustand aktualisieren
    state = update_state(state, user_input)

    # 2️⃣ ECTS-Hinweis (nur einmal pro Studiengang)
    ects_info = get_ects_info(state, RULES)
    if ects_info:
        return {"response": ects_info, "progress": SESSIONS[user_id]["progress"], "options": None}

    # 3️⃣ Nächste Frage holen
    question = get_next_question(state)
    if question:
        text = question["text"]
        options = question.get("options")

        # Fortschritt berechnen
        answered = len([k for k in state.keys() if k in [q["key"] for q in questions]])
        total = len([q for q in questions if condition_met(state, q)])
        progress = int((answered / total) * 100)
        SESSIONS[user_id]["progress"] = progress

        return {"response": text, "progress": progress, "options": options}

    # 4️⃣ Wenn keine Frage mehr → Entscheidung berechnen
    category = state.get("nutzerkategorie")
    if category == "bachelor":
        decision, explanation = evaluate_bachelor(state)
    elif category == "master_intern":
        decision, explanation = evaluate_master_intern(state, RULES["Allgemein"])
    elif category == "master_extern":
        program = state.get("studiengang")
        program_rules = RULES["Studiengänge"].get(program, {}).get("ECTS_Anforderungen", {})
        decision, explanation = evaluate_master_extern(state, program_rules, RULES["Allgemein"])
    else:
        decision, explanation = "Unklar", "Keine ausreichenden Angaben."

    # Logging
    try:
        log_event({
            "user_id": user_id,
            "nutzerkategorie": category,
            "studiengang": state.get("studiengang"),
            "abschlussziel": state.get("abschlussziel"),
            "entscheidung": decision,
            "completed": True
        })
    except Exception as e:
        print(f"[WARN] Logging fehlgeschlagen: {e}")

    # Session löschen
    SESSIONS.pop(user_id, None)

    return {
        "response": f"📋 Entscheidung: {decision}\n\n{explanation}",
        "progress": 100,
        "options": None
    }


@app.get("/")
def home():
    return {"status": "Bifi Backend läuft 🚀", "sessions": len(SESSIONS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
