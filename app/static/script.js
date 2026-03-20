
// async function sendMessage() {
//   const input = document.getElementById("user-input");
//   const chatBox = document.getElementById("chat-box");

//   const userMessage = input.value.trim();
//   if (!userMessage) return;

//   chatBox.innerHTML += `<div class="user">You: ${userMessage}</div>`;
//   input.value = "";
//   chatBox.scrollTop = chatBox.scrollHeight;

//   try {
//     const response = await fetch("/chat", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ message: userMessage })
//     });

//     const data = await response.json();

//     // ✅ Ensure answer is string
//     let botReply = data.answer;

//     if (typeof botReply === "object") {
//       botReply = JSON.stringify(botReply);
//     }

//     chatBox.innerHTML += `<div class="bot">🤖: ${botReply}</div>`;
//     chatBox.scrollTop = chatBox.scrollHeight;

//   } catch (error) {
//     chatBox.innerHTML += `<div class="bot">❌ Error: ${error}</div>`;
//   }
// }


function initChat() {
  const messagesEl = document.getElementById("messages");
  const questionInput = document.getElementById("question");
  const sendBtn = document.getElementById("sendBtn");

  if (!messagesEl || !questionInput || !sendBtn) {
    console.error(
      "Missing required elements. Check IDs: messages, question, sendBtn."
    );
    return;
  }

  function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = text;
  wrapper.appendChild(bubble);
  messagesEl.appendChild(wrapper);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  async function sendQuestion() {
  const q = questionInput.value.trim();
  if (!q) return;
  addMessage("you", q);
  questionInput.value = "";

  addMessage("bot", "<em>Searching documents...</em>");

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: q }),
    });
    const data = await res.json();
    // replace loading message with actual answer
    messagesEl.lastChild.remove();
    addMessage("bot", data.answer);
  } catch (e) {
    messagesEl.lastChild.remove();
    addMessage("bot", "Error contacting server.");
  }
  }

  sendBtn.addEventListener("click", sendQuestion);
  questionInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendQuestion();
  });
}

window.addEventListener("DOMContentLoaded", initChat);