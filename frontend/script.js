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

function appendMessage(sender, text, options = null) {
  const msg = document.createElement("div");
  msg.classList.add("message", sender === "user" ? "user-msg" : "bot-msg");
  msg.innerHTML = text.replace(/\n/g, "<br>");
  chatWindow.appendChild(msg);

  if (options && Array.isArray(options)) {
    const buttonContainer = document.createElement("div");
    buttonContainer.className = "button-container";
    options.forEach(option => {
      const btn = document.createElement("button");
      btn.className = "option-button";
      btn.textContent = option;
      btn.onclick = () => {
        sendMessage(option);
        buttonContainer.remove();
      };
      buttonContainer.appendChild(btn);
    });
    chatWindow.appendChild(buttonContainer);
  }
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function updateProgress(value) {
  progressBar.style.height = `${value}%`;
  progressText.innerHTML = `${value}%<br>Fortschritt`;
  if (value >= 100) enableApplyButton();
}

function enableApplyButton() {
  applyBtn.classList.remove("disabled");
  applyBtn.classList.add("success");
  applyBtn.disabled = false;
}

function showHelp() {
  alert("💡 Hilfe & FAQ\n\nIch begleite Sie Schritt für Schritt durch den Zulassungscheck für Masterstudiengänge der HSBI.\n\n👉 Klicken Sie auf START, um zu beginnen.\n👉 Wählen Sie aus den Vorschlägen oder geben Sie Ihre Antwort manuell ein.");
}

function showApplyPopup() {
  alert("🎓 Sie erfüllen die Voraussetzungen!\n\nHier geht’s zur Bewerbung: https://www.hsbi.de/masterbewerbung");
}

async function sendMessage(message) {
  appendMessage("user", message);
  inputField.value = "";
  appendMessage("bot", "💭 Einen Moment bitte...");

  try {
    const res = await fetch("http://127.0.0.1:5000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    const data = await res.json();
    const loading = document.querySelector(".bot-msg:last-child");
    if (loading && loading.textContent.includes("Einen Moment")) loading.remove();

    if (data.ects_info) appendMessage("bot", data.ects_info);

    if (data.type === "question") {
      appendMessage("bot", data.text, data.options || null);
      progress = Math.min(progress + 15, 100);
      updateProgress(progress);
    } else if (data.type === "decision") {
      appendMessage("bot", `📋 <b>Ergebnis:</b> ${data.entscheidung}<br>${data.begruendung}`);
      updateProgress(100);
      enableApplyButton();
    } else {
      appendMessage("bot", "⚠️ Unerwartete Antwort vom Server.");
    }
  } catch (err) {
    appendMessage("bot", "🚫 Fehler bei der Serververbindung. Bitte Backend starten!");
    console.error(err);
  }
}

startBtn.addEventListener("click", () => {
  chatWindow.innerHTML = "";
  progress = 0;
  updateProgress(0);
  appendMessage("bot", "Willkommen! Ich bin Bifi 👋 – dein Studienberater. Für welchen Abschluss interessierst du dich?");
});

sendBtn.addEventListener("click", () => {
  if (inputField.value.trim() !== "") sendMessage(inputField.value.trim());
});

helpBtn.addEventListener("click", showHelp);
applyBtn.addEventListener("click", showApplyPopup);
