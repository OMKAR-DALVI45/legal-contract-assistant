import time
import uuid
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

documents = {}          # temporary store: doc_id -> details
MAX_MB = 20


def fake_processing(doc_id: str):
    """Pretend to chunk and embed the file, then mark it ready."""
    time.sleep(3)
    if doc_id in documents:
        documents[doc_id]["status"] = "ready"


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.post("/documents")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are allowed")

    content = await file.read()
    if len(content) > MAX_MB * 1024 * 1024:
        raise HTTPException(413, f"File is too large (max {MAX_MB} MB)")

    doc_id = str(uuid.uuid4())
    documents[doc_id] = {
        "name": file.filename,
        "size": len(content),
        "status": "processing",
        "uploaded_at": datetime.now().strftime("%H:%M:%S"),
        "content": content,                     # file bytes, kept in memory for now
    }

    background_tasks.add_task(fake_processing, doc_id)
    return {"doc_id": doc_id, "name": file.filename, "status": "processing"}


@app.get("/documents")
def list_documents():
    # return details only, never the file bytes
    return [
        {
            "id": doc_id,
            "name": d["name"],
            "size": d["size"],
            "status": d["status"],
            "uploaded_at": d["uploaded_at"],
        }
        for doc_id, d in documents.items()
    ]