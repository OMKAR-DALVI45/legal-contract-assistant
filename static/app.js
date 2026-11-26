const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const statusEl = document.getElementById("uploadStatus");
const docList = document.getElementById("docList");
const uploadBtn = document.getElementById("uploadButton");
const chatForm = document.getElementById("chatForm");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendButton");
const messagesEl = document.getElementById("chatMessages");

const MAX_MB = 20;
let pollTimer = null;

function setStatus(message, type = "") {
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function errorText(data) {
  if (!data || !data.detail) return "Something went wrong";
  if (typeof data.detail === "string") return data.detail;
  return data.detail.map(item => item.msg || item).join(", ");
}

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0]?.name || "Click to choose a PDF";
  setStatus("");
});
uploadBtn.addEventListener("click", upload);

async function upload() {
  const file = fileInput.files[0];
  if (!file) return setStatus("Choose a PDF first", "error");
  if (!file.name.toLowerCase().endsWith(".pdf")) return setStatus("Only PDF files are allowed", "error");
  if (file.size > MAX_MB * 1024 * 1024) return setStatus(`File is too large (max ${MAX_MB} MB)`, "error");
  const formData = new FormData();
  formData.append("file", file);
  uploadBtn.disabled = true;
  setStatus("Uploading and starting PDF indexing…");
  try {
    const response = await fetch("/documents", { method: "POST", body: formData });
    const data = await response.json().catch(() => null);
    if (!response.ok) return setStatus(`Error: ${errorText(data)}`, "error");
    setStatus(`Uploaded ${data.name}. Extracting and indexing text…`, "ok");
    fileInput.value = "";
    fileName.textContent = "Click to choose a PDF";
    await loadDocuments();
  } catch {
    setStatus("Could not reach the server. Is it running?", "error");
  } finally {
    uploadBtn.disabled = false;
  }
}

async function loadDocuments() {
  try {
    const response = await fetch("/documents");
    if (!response.ok) throw new Error("Could not load documents");
    const docs = await response.json();
    renderDocuments(docs);
    clearTimeout(pollTimer);
    if (docs.some(doc => doc.status === "processing")) pollTimer = setTimeout(loadDocuments, 2000);
  } catch {
    docList.textContent = "Could not load documents";
  }
}

function renderDocuments(docs) {
  docList.replaceChildren();
  if (!docs.length) {
    const empty = document.createElement("li");
    empty.textContent = "No documents yet";
    docList.appendChild(empty);
    return;
  }
  for (const doc of docs) {
    const item = document.createElement("li");
    const info = document.createElement("span");
    info.textContent = `${doc.name} (${formatSize(doc.size)})`;
    const badge = document.createElement("span");
    badge.className = `badge ${doc.status}`;
    badge.textContent = doc.status;
    item.append(info, badge);
    docList.appendChild(item);
  }
}

function addMessage(text, kind) {
  const message = document.createElement("div");
  message.className = `message ${kind}`;
  const body = document.createElement("p");
  body.textContent = text;
  message.appendChild(body);
  messagesEl.appendChild(message);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return message;
}

chatForm.addEventListener("submit", async event => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;
  addMessage(question, "user-message");
  questionInput.value = "";
  sendBtn.disabled = true;
  const pending = addMessage("Searching your documents…", "assistant-message pending");
  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await response.json().catch(() => null);
    pending.remove();
    if (!response.ok) {
      addMessage(errorText(data), "assistant-message error-message");
      return;
    }
    const answer = addMessage(data.answer, "assistant-message");
    if (data.sources?.length) {
      const sourceList = document.createElement("ul");
      sourceList.className = "sources";
      for (const source of data.sources) {
        const item = document.createElement("li");
        item.textContent = `[${source.citation}] ${source.document_name}, page ${source.page}: ${source.excerpt}`;
        sourceList.appendChild(item);
      }
      answer.appendChild(sourceList);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }
  } catch {
    pending.remove();
    addMessage("Could not reach the answer service. Check that the backend is running.", "assistant-message error-message");
  } finally {
    sendBtn.disabled = false;
    questionInput.focus();
  }
});

loadDocuments();
