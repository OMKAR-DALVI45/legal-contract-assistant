// ---------- Elements ----------
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const statusEl = document.getElementById("uploadStatus");
const docList = document.getElementById("docList");
const uploadBtn = document.querySelector(".btn");

const MAX_MB = 20;
let pollTimer = null;

// ---------- Helpers ----------
function setStatus(message, type = "") {
  statusEl.textContent = message;
  statusEl.className = "status " + type;       // "", "ok" or "error"
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

// FastAPI errors look like {detail: "text"} or {detail: [{msg: "..."}]}
function errorText(data) {
  if (!data || !data.detail) return "Something went wrong";
  if (typeof data.detail === "string") return data.detail;
  return data.detail.map(d => d.msg).join(", ");
}

// ---------- Show the chosen file name ----------
fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  fileName.textContent = file ? file.name : "Click to choose a PDF";
  setStatus("");
});

// ---------- Upload: send the file to FastAPI ----------
async function upload() {
  const file = fileInput.files[0];

  if (!file) {
    setStatus("Choose a PDF first", "error");
    return;
  }
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    setStatus("Only PDF files are allowed", "error");
    return;
  }
  if (file.size > MAX_MB * 1024 * 1024) {
    setStatus(`File is too large (max ${MAX_MB} MB)`, "error");
    return;
  }

  const form = new FormData();
  form.append("file", file);                   // must match the FastAPI parameter name

  uploadBtn.disabled = true;
  setStatus("Uploading...");

  try {
    const res = await fetch("/documents", { method: "POST", body: form });
    const data = await res.json().catch(() => null);

    if (!res.ok) {
      setStatus("Error: " + errorText(data), "error");
      return;
    }

    setStatus("Uploaded: " + data.name, "ok");
    fileInput.value = "";
    fileName.textContent = "Click to choose a PDF";
    await loadDocuments();
  } catch (err) {
    setStatus("Could not reach the server. Is it running?", "error");
  } finally {
    uploadBtn.disabled = false;
  }
}

// ---------- Get the list from FastAPI ----------
async function loadDocuments() {
  try {
    const res = await fetch("/documents");
    if (!res.ok) throw new Error("failed");
    const docs = await res.json();
    renderDocuments(docs);

    // keep checking while any document is still processing
    clearTimeout(pollTimer);
    if (docs.some(d => d.status === "processing")) {
      pollTimer = setTimeout(loadDocuments, 2000);
    }
  } catch (err) {
    docList.textContent = "Could not load documents";
  }
}

// ---------- Draw the list on the page ----------
function renderDocuments(docs) {
  docList.innerHTML = "";

  if (docs.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No documents yet";
    docList.appendChild(li);
    return;
  }

  docs.forEach(doc => {
    const li = document.createElement("li");

    const info = document.createElement("span");
    info.textContent = `${doc.name} (${formatSize(doc.size)}, ${doc.uploaded_at})`;

    const badge = document.createElement("span");
    badge.className = "badge " + doc.status;
    badge.textContent = doc.status;

    li.appendChild(info);
    li.appendChild(badge);
    docList.appendChild(li);
  });
}

// ---------- Start ----------
loadDocuments();