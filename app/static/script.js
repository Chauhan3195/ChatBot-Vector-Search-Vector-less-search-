function initChat() {
  const messagesEl = document.getElementById("messages");
  const questionInput = document.getElementById("question");
  const sendBtn = document.getElementById("sendBtn");
  const historyListEl = document.getElementById("historyList");
  const newChatBtn = document.getElementById("newChatBtn");
  const clearAllChatsBtn = document.getElementById("clearAllChatsBtn");
  const fileInput = document.getElementById("pdfFile");
  const uploadBtn = document.getElementById("uploadBtn");

  if (uploadBtn && fileInput) {
    uploadBtn.addEventListener("click", async () => {
      const loader = document.getElementById("globalLoader");
      console.log(loader);
      const files = fileInput.files;
    
      if (!files.length) {
        alert("Please select at least one PDF file");
        return;
      }
      // Show loader
      loader.style.display = "flex";
      const formData = new FormData();
    
      // append multiple files
      for (let i = 0; i < files.length; i++) {
        formData.append("files", files[i]); // IMPORTANT: "files"
      }
    
      try {
        const res = await fetch("/upload", {
          method: "POST",
          body: formData,
        });
    
        const data = await res.json();
    
        alert(data.message || "Files uploaded successfully");
    
        fileInput.value = "";
    
        // reload file list after upload
        loadFiles();
      } catch (err) {
        console.error(err);
        alert("Upload failed");
      } finally {
        //  Hide loader after response
        loader.style.display = "none";
      }
    });
  }

  const fileListEl = document.getElementById("fileList");
//addde
  async function loadFiles() {
    try {
      const res = await fetch("/files");
      const data = await res.json();
  
      fileListEl.innerHTML = "";
  
      data.files.forEach((file) => {
        const li = document.createElement("li");
        li.classList.add("file-item");
  
        // filename span
        const span = document.createElement("span");
        span.textContent = file;
  
        // delete button
        const delBtn = document.createElement("button");
        delBtn.textContent = "❌";
        delBtn.style.marginLeft = "10px";
  
        // pass button to deleteFile
        delBtn.onclick = () => deleteFile(file, delBtn);
  
        li.appendChild(span);
        li.appendChild(delBtn);
        fileListEl.appendChild(li);
      });
    } catch (err) {
      console.error("Error loading files", err);
    }
  }
///end 
  if (!messagesEl || !questionInput || !sendBtn) {
    console.error(
      "Missing required elements. Check IDs: messages, question, sendBtn."
    );
    return;
  }


  function deleteFile(file, btn) {
    // Find the parent <li> of this button
    const li = btn.closest(".file-item");
  
    // Remove immediately from UI
    if (li) li.remove();
  
    // Call backend in background
    fetch(`/delete/${encodeURIComponent(file)}`, {
      method: "DELETE",
    })
      .then(res => res.json())
      .then(data => console.log("Deleted:", data))
      .catch(err => {
        console.error("Delete failed", err);
        alert("Delete failed, refreshing...");
        location.reload();
      });
  }

  const STORAGE_KEY = "rag_chat_history_v1";

  // { id, title, createdAt, updatedAt, messages: [{role, text, ts}] }
  let conversations = [];
  let activeConversationId = null;

  function saveState() {
    try {
      const payload = { conversations, activeConversationId };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (e) {
      // If storage is full/blocked, keep chat working without persistence
      console.warn("Failed to save chat history:", e);
    }
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      conversations = Array.isArray(parsed.conversations) ? parsed.conversations : [];
      activeConversationId =
        typeof parsed.activeConversationId === "number" ? parsed.activeConversationId : null;
    } catch (e) {
      console.warn("Failed to load chat history:", e);
    }
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
    return wrapper;
  }

  function clearMessagesUI() {
    messagesEl.innerHTML = "";
  }

  function getActiveConversation() {
    return conversations.find((c) => c.id === activeConversationId) || null;
  }

  function makeTitleFromText(text) {
    const t = (text || "").trim();
    if (!t) return "New Chat";
    return t.length > 32 ? `${t.slice(0, 29).trimEnd()}...` : t;
  }

  function createConversation(title) {
    const now = Date.now();
    const conv = {
      id: now, // good enough for single-user local UI
      title: makeTitleFromText(title),
      createdAt: now,
      updatedAt: now,
      messages: [],
    };
    conversations.unshift(conv);
    activeConversationId = conv.id;
    saveState();
    renderHistory();
    clearMessagesUI();
    return conv;
  }

  function setActiveConversation(id) {
    activeConversationId = id;
    const conv = getActiveConversation();
    clearMessagesUI();
    if (conv) {
      conv.messages.forEach((m) => addMessage(m.role, m.text));
    }
    saveState();
    renderHistory();
  }

  function deleteConversation(id) {
    const idx = conversations.findIndex((c) => c.id === id);
    if (idx === -1) return;

    conversations.splice(idx, 1);

    if (activeConversationId === id) {
      activeConversationId = conversations.length > 0 ? conversations[0].id : null;
      clearMessagesUI();
      if (activeConversationId) {
        const conv = getActiveConversation();
        conv.messages.forEach((m) => addMessage(m.role, m.text));
      }
    }

    saveState();
    renderHistory();
  }

  function clearAllChats() {
    conversations = [];
    activeConversationId = null;
    clearMessagesUI();
    saveState();
    renderHistory();
  }

  function renderHistory() {
    if (!historyListEl) return;
    historyListEl.innerHTML = "";

    conversations.forEach((conv) => {
      const li = document.createElement("li");
      li.className = `history-item ${conv.id === activeConversationId ? "active" : ""}`.trim();

      const titleSpan = document.createElement("span");
      titleSpan.className = "history-title";
      titleSpan.textContent = conv.title;
      titleSpan.title = conv.title;

      const actions = document.createElement("span");
      actions.className = "history-actions";

      const delBtn = document.createElement("button");
      delBtn.className = "icon-btn";
      delBtn.type = "button";
      delBtn.title = "Delete chat";
      delBtn.textContent = "🗑";
      delBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        deleteConversation(conv.id);
      });

      actions.appendChild(delBtn);
      li.appendChild(titleSpan);
      li.appendChild(actions);

      li.addEventListener("click", () => setActiveConversation(conv.id));
      historyListEl.appendChild(li);
    });
  }

  async function sendQuestion() {
  const q = questionInput.value.trim();
  if (!q) return;
  let conv = getActiveConversation();
  if (!conv) {
    conv = createConversation(q);
  }

  addMessage("you", q);
  conv.messages.push({ role: "you", text: q, ts: Date.now() });
  // ADD THIS BLOCK HERE ONLY
  if (conv.messages.length === 1) {
    conv.title = makeTitleFromText(q);
  }
  conv.updatedAt = Date.now();
  questionInput.value = "";
  saveState();

  let dots = 0;
  const loadingEl = addMessage("bot", "<em>Searching documents.</em>");
  const loadingBubble = loadingEl.querySelector(".bubble");
  const loadingInterval = window.setInterval(() => {
    dots = (dots % 3) + 1;
    const line = `Searching documents${".".repeat(dots)}`;
    if (loadingBubble) loadingBubble.innerHTML = `<em>${line}</em>`;
  }, 350);

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: q }),
    });
    const data = await res.json();

    window.clearInterval(loadingInterval);
    loadingEl.remove();

    addMessage("bot", data.answer);
    conv.messages.push({ role: "bot", text: data.answer, ts: Date.now() });
    conv.updatedAt = Date.now();
    saveState();
    renderHistory();
  } catch (e) {

    window.clearInterval(loadingInterval);
    loadingEl.remove();

    addMessage("bot", "Error contacting server.");
    conv.messages.push({ role: "bot", text: "Error contacting server.", ts: Date.now() });
    conv.updatedAt = Date.now();
    saveState();
    renderHistory();
  }
  }

  sendBtn.addEventListener("click", sendQuestion);
  questionInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendQuestion();
  });

  if (newChatBtn) {
    newChatBtn.addEventListener("click", () => createConversation("New Chat"));
  }
  if (clearAllChatsBtn) {
    clearAllChatsBtn.addEventListener("click", () => {
      const ok = window.confirm("Clear all chats? This cannot be undone.");
      if (ok) clearAllChats();
    });
  }

  loadState();
  renderHistory();
  loadFiles();
  if (activeConversationId) {
    setActiveConversation(activeConversationId);
  }
}

window.addEventListener("DOMContentLoaded", initChat);
