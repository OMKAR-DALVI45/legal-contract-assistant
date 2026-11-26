import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
#from openai import APIError
from sqlalchemy.exc import SQLAlchemyError

from app.database import (
    close_database,
    initialize_database,
    list_documents as query_documents,
    save_document,
    set_document_status,
)
from app.rag import answer_question, index_pdf
from app.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
MAX_MB = 20


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        initialize_database()
    except SQLAlchemyError as exc:
        raise RuntimeError("Could not initialize PostgreSQL. Check DATABASE_URL and database access.") from exc
    yield
    close_database()


app = FastAPI(title="Legal Contract Assistant", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def process_document(document_id: str, filename: str, content: bytes) -> None:
    try:
        index_pdf(document_id, filename, content)
        set_document_status(document_id, "ready")
    except Exception:
        logger.exception("Failed to extract or index document %s", document_id)
        try:
            set_document_status(document_id, "failed")
        except SQLAlchemyError:
            logger.exception("Failed to update status for document %s", document_id)


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/documents")
def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        file.file.close()
        raise HTTPException(400, "Only PDF files are allowed")

    try:
        content = file.file.read(MAX_MB * 1024 * 1024 + 1)
        if len(content) > MAX_MB * 1024 * 1024:
            raise HTTPException(413, f"File is too large (max {MAX_MB} MB)")
        try:
            document_id, _uploaded_at = save_document(file.filename, content)
        except SQLAlchemyError as exc:
            raise HTTPException(503, "Could not save the document to PostgreSQL") from exc
    finally:
        file.file.close()

    background_tasks.add_task(process_document, document_id, file.filename, content)
    return {"doc_id": document_id, "name": file.filename, "status": "processing"}


@app.get("/documents")
def get_documents():
    try:
        rows = query_documents()
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Could not load documents from PostgreSQL") from exc
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "size": row["size"],
            "status": row["status"],
            "uploaded_at": row["uploaded_at"].astimezone().strftime("%H:%M:%S %Z"),
        }
        for row in rows
    ]


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(422, "Question cannot be blank")
    try:
        return answer_question(question)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except APIError as exc:
        logger.exception("Groq request failed")
        raise HTTPException(502, "The answer service could not complete the request") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
