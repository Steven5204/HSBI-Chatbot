const chatWindow = document.getElementById("chat-window");
const inputField = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

async function sendMessage() {
  const userText = inputField.value.trim();
  if (!userText) return;

  appendMessage("user", userText);
  inputField.value = "";
  inputField.disabled = true;
  sendBtn.disabled = true;

  appendMessage("bot", "💭 Einen Moment bitte...");

  try {
    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userText }),
    });

    const data = await res.json();

    // Entferne "wird geschrieben..." Nachricht
    const loadingBubble = document.querySelector(".bot-msg:last-child");
    if (loadingBubble) loadingBubble.remove();

    appendMessage("bot", data.response || "⚠️ Keine Antwort vom Server erhalten.");
  } catch (error) {
    appendMessage("bot", "❌ Fehler bei der Serververbindung.");
    console.error("API Error:", error);
  } finally {
    inputField.disabled = false;
    sendBtn.disabled = false;
    inputField.focus();
  }
}

function appendMessage(sender, text) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", sender === "user" ? "user-msg" : "bot-msg");
  messageDiv.textContent = text;
  chatWindow.appendChild(messageDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Event Listeners
sendBtn.addEventListener("click", sendMessage);
inputField.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});
