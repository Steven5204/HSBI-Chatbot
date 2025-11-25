const chatWindow = document.getElementById("chat-window");
const inputField = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const startBtn = document.getElementById("start-btn");
const helpBtn = document.getElementById("help-btn");
const applyBtn = document.getElementById("apply-btn");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");

let userId = crypto.randomUUID();

function appendMessage(sender, text) {
  const msg = document.createElement("div");
  msg.classList.add("message", sender === "user" ? "user-msg" : "bot-msg");
  msg.textContent = text;
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function updateProgress(percent) {
  progressBar.style.height = `${percent}%`;
  progressText.textContent = `${percent}%\nFortschritt`;
  if (percent === 100) enableApplyButton();
}

function enableApplyButton() {
  applyBtn.classList.remove("disabled");
  applyBtn.classList.add("success");
  applyBtn.disabled = false;
}

function showHelp() {
  alert(
    "💡 Hilfe & FAQ\n\nIch begleite Sie Schritt für Schritt durch die Zulassungsvoraussetzungen für ein berufsbegleitendes Masterstudium.\n\n👉 Klicken Sie auf START, um zu beginnen.\n👉 Wählen Sie aus den Vorschlägen oder geben Sie Ihre Antwort manuell ein."
  );
}

function showApplyPopup() {
  alert("🎓 Sie erfüllen die Voraussetzungen!\n\nHier geht’s zur Bewerbung: https://www.hsbi.de/masterbewerbung");
}

async function sendMessage(message) {
  appendMessage("user", message);
  inputField.value = "";

  appendMessage("bot", "💭 Einen Moment bitte...");

  const res = await fetch("http://127.0.0.1:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, user_id: userId }),
  });

  const data = await res.json();

  // Entferne Lade-Bubble
  const loading = document.querySelector(".bot-msg:last-child");
  if (loading && loading.textContent.includes("Einen Moment")) loading.remove();

  appendMessage("bot", data.response);
  updateProgress(data.progress || 0);
}

startBtn.addEventListener("click", () => {
  chatWindow.innerHTML = "";
  appendMessage(
    "bot",
    "Willkommen! Ich bin dein Assistent für die Zulassung zum Masterstudiengang. Klicke auf 'Start', um zu beginnen."
  );
  sendMessage("Start");
});

sendBtn.addEventListener("click", () => {
  if (inputField.value.trim() !== "") sendMessage(inputField.value.trim());
});

helpBtn.addEventListener("click", showHelp);
applyBtn.addEventListener("click", showApplyPopup);
