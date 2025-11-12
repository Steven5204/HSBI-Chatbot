// --- Referenzen auf HTML-Elemente ---
const chatWindow = document.getElementById("chat-window");
const inputField = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

function formatMarkdown(text) {
  // Einfache Markdown-Formatierung ersetzen
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>") // Fett
    .replace(/\n/g, "<br>") // Zeilenumbrüche
    .replace(/✅/g, "✅")   // Emojis beibehalten
    .replace(/➡️/g, "➡️"); // Pfeile beibehalten
}

// --- Hilfsfunktionen ---
function appendMessage(sender, text) {
  const msgDiv = document.createElement("div");
  msgDiv.classList.add("message", sender === "user" ? "user-msg" : "bot-msg");
  msgDiv.innerHTML = sender === "bot" ? formatMarkdown(text) : text; // HTML für Bot
  chatWindow.appendChild(msgDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Call setProgress(percent) from your chat logic (upload progress, model completion, etc.)
  function clamp(n){ return Math.max(0, Math.min(100, n)); }

   function setProgress(percent) {
    const p = clamp(Math.round(percent));
    const fill = document.getElementById('progress-fill');
    const label = document.getElementById('progress-label');
    const wrap = document.querySelector('#chat-progress .progress-wrap');

    if (!fill || !label || !wrap) return;
    fill.style.width = p + '%';
    label.textContent = p + '%';
    wrap.setAttribute('aria-valuenow', String(p));

    // optional: hide when done
    if (p >= 100) {
      setTimeout(()=> { document.getElementById('chat-progress').style.display = 'none'; }, 450);
    } else {
      document.getElementById('chat-progress').style.display = '';
    }
  }

// 🔹 Immer neue Session-ID bei Seitenaufruf
let userId = crypto.randomUUID();
console.log("Neue Sitzung gestartet:", userId);

// --- Willkommensnachricht beim Laden ---
window.addEventListener("DOMContentLoaded", async () => {
  appendMessage("bot", "💬 Initialisiere Chat...");

  try {
    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: "init", // löst im Backend den Begrüßungsflow aus
        user_id: userId, // neue Sitzung
      }),
    });

    const data = await res.json();
    const welcome = data.response || "👋 Willkommen! Ich helfe Ihnen beim Studiencheck.";
    document.querySelector(".bot-msg:last-child").remove(); // "Initialisiere..." löschen
    appendMessage("bot", welcome);
    updateProgress(data.progress || 0);
  } catch (err) {
    appendMessage("bot", "❌ Verbindung zum Server fehlgeschlagen.");
    console.error(err);
  }
});


// --- Nachricht senden ---
async function sendMessage() {
  const userText = inputField.value.trim();
  if (!userText) return;

  appendMessage("user", userText);
  inputField.value = "";
  inputField.disabled = true;
  sendBtn.disabled = true;

  // Zeige "Denken..." Nachricht
  appendMessage("bot", "💭 Einen Moment bitte...");

  try {
    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userText,
        user_id: userId, 
      }),
    });

    const data = await res.json();

    // 🔹 Entferne die "Einen Moment..." Nachricht (falls vorhanden)
    const loadingBubble = document.querySelector(".bot-msg:last-child");
    if (loadingBubble && loadingBubble.textContent.includes("Einen Moment")) {
      loadingBubble.remove();
    }

    // Zeige Bot-Antwort
    appendMessage("bot", data.response || "⚠️ Keine Antwort erhalten.");

    // Fortschritt aktualisieren
    updateProgress(data.progress || 0);

  } catch (error) {
    appendMessage("bot", "❌ Fehler bei der Verbindung zum Server.");
    console.error("API Error:", error);
  } finally {
    inputField.disabled = false;
    sendBtn.disabled = false;
    inputField.focus();
  }
}

// --- Event Listener ---
sendBtn.addEventListener("click", sendMessage);
inputField.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});

function updateProgress(percent) {
  const fill = document.getElementById("progress-fill");
  const text = document.getElementById("progress-text");

  if (fill) fill.style.width = `${percent}%`;
  if (text) text.textContent = `Fortschritt: ${percent}%`;
}
