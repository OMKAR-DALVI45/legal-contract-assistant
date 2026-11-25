import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import BigInteger, Column, DateTime, LargeBinary, MetaData, String, Table, create_engine, select, update
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is missing. Add your PostgreSQL connection string to .env.")

engine = create_engine(database_url, pool_pre_ping=True)
metadata = MetaData()
uploaded_documents = Table(
    "uploaded_documents",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("name", String(255), nullable=False),
    Column("size", BigInteger, nullable=False),
    Column("status", String(20), nullable=False, default="processing"),
    Column("uploaded_at", DateTime(timezone=True), nullable=False),
    Column("content", LargeBinary, nullable=False),
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        metadata.create_all(engine)
    except SQLAlchemyError as exc:
        raise RuntimeError("Could not initialize PostgreSQL. Check DATABASE_URL and database access.") from exc
    yield
    engine.dispose()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
MAX_MB = 20


def finish_processing(doc_id: str):
    """Keep the prototype's simulated processing status, persisted in PostgreSQL."""
    time.sleep(3)
    try:
        with engine.begin() as conn:
            conn.execute(
                update(uploaded_documents)
                .where(uploaded_documents.c.id == doc_id)
                .values(status="ready")
            )
    except SQLAlchemyError:
        # The document remains safely stored as "processing" if this status update fails.
        return


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.post("/documents")
def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        file.file.close()
        raise HTTPException(400, "Only PDF files are allowed")

    try:
        content = file.file.read(MAX_MB * 1024 * 1024 + 1)
        if len(content) > MAX_MB * 1024 * 1024:
            raise HTTPException(413, f"File is too large (max {MAX_MB} MB)")

        doc_id = str(uuid.uuid4())
        uploaded_at = datetime.now(timezone.utc)
        try:
            with engine.begin() as conn:
                conn.execute(
                    uploaded_documents.insert().values(
                        id=doc_id,
                        name=file.filename,
                        size=len(content),
                        status="processing",
                        uploaded_at=uploaded_at,
                        content=content,
                    )
                )
        except SQLAlchemyError as exc:
            raise HTTPException(503, "Could not save the document to PostgreSQL") from exc
    finally:
        file.file.close()

    background_tasks.add_task(finish_processing, doc_id)
    return {"doc_id": doc_id, "name": file.filename, "status": "processing"}


@app.get("/documents")
def list_documents():
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                select(
                    uploaded_documents.c.id,
                    uploaded_documents.c.name,
                    uploaded_documents.c.size,
                    uploaded_documents.c.status,
                    uploaded_documents.c.uploaded_at,
                ).order_by(uploaded_documents.c.uploaded_at.desc())
            ).mappings().all()
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Could not load documents from PostgreSQL") from exc

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "size": row["size"],
            "status": row["status"],
            "uploaded_at": row["uploaded_at"].astimezone(timezone.utc).strftime("%H:%M:%S UTC"),
        }
        for row in rows
    ]
