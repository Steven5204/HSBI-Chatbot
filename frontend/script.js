// === Globale Elemente ===
const chatWindow = document.getElementById("chat-window");
const inputField = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const startBtn = document.getElementById("start-btn");
const helpBtn = document.getElementById("help-btn");
const applyBtn = document.getElementById("apply-btn");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");

let sessionId = crypto.randomUUID();
let progress = 0;

// === Nachricht in den Chat schreiben ===
function appendMessage(sender, text) {
  const msg = document.createElement("div");
  msg.classList.add("message", sender === "user" ? "user-msg" : "bot-msg");
  msg.innerHTML = text.replace(/\n/g, "<br>");
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// === Fortschritt aktualisieren ===
function updateProgress(value) {
  progressBar.style.height = `${value}%`;
  progressText.innerHTML = `${value}%<br>Fortschritt`;
}

// === Buttons anzeigen ===
function showOptionButtons(options) {
  if (!options || !Array.isArray(options)) return;
  const buttonContainer = document.createElement("div");
  buttonContainer.classList.add("button-container");

  options.forEach((option) => {
    const btn = document.createElement("button");
    btn.classList.add("option-button");
    btn.textContent = option;
    btn.onclick = () => {
      sendMessage(option);
      buttonContainer.remove();
    };
    buttonContainer.appendChild(btn);
  });

  chatWindow.appendChild(buttonContainer);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// === Nachricht an Backend senden ===
async function sendMessage(message) {
  appendMessage("user", message);

  try {
    const response = await fetch("http://127.0.0.1:5000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, user_id: sessionId }),
    });

    const data = await response.json();

    if (data.response) {
      appendMessage("bot", data.response);

      // 🔹 Wenn Optionen vorhanden → Buttons anzeigen
      if (data.options && Array.isArray(data.options) && data.options.length > 0) {
        showOptionButtons(data.options);
      }

      // 🔹 Fortschrittsanzeige aktualisieren
      if (data.progress !== undefined) {
        updateProgress(data.progress);
      }
    }
  } catch (err) {
    appendMessage("bot", "🚫 Fehler bei der Serververbindung.");
    console.error(err);
  }
}

// === Buttons ===
startBtn.addEventListener("click", () => {
  chatWindow.innerHTML = "";
  progress = 0;
  updateProgress(0);
  appendMessage("bot", "Willkommen! Ich bin Bifi 👋 – dein Studienberater. Für welchen Abschluss interessierst du dich?");
  // 🔹 Zeige direkt die erste Frage-Optionen
  showOptionButtons(["Bachelor", "Master"]);
});

sendBtn.addEventListener("click", () => {
  const msg = inputField.value.trim();
  if (msg) {
    sendMessage(msg);
    inputField.value = "";
  }
});

helpBtn.addEventListener("click", () => {
  appendMessage(
    "bot",
    "💡 Hilfe & FAQ:<br>Ich begleite dich Schritt für Schritt durch den Zulassungscheck.<br>Drücke <b>Start</b>, um zu beginnen."
  );
});

applyBtn.addEventListener("click", () => {
  window.open("https://www.hsbi.de/masterbewerbung", "_blank");
});
