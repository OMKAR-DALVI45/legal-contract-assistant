import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import BigInteger, Column, DateTime, LargeBinary, MetaData, String, Table, create_engine, insert, select, update
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


def initialize_database() -> None:
    metadata.create_all(engine)


def save_document(name: str, content: bytes) -> tuple[str, datetime]:
    document_id = str(uuid.uuid4())
    uploaded_at = datetime.now(timezone.utc)
    with engine.begin() as connection:
        connection.execute(
            insert(uploaded_documents).values(
                id=document_id,
                name=name,
                size=len(content),
                status="processing",
                uploaded_at=uploaded_at,
                content=content,
            )
        )
    return document_id, uploaded_at


def set_document_status(document_id: str, status: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            update(uploaded_documents)
            .where(uploaded_documents.c.id == document_id)
            .values(status=status)
        )


def list_documents() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            select(
                uploaded_documents.c.id,
                uploaded_documents.c.name,
                uploaded_documents.c.size,
                uploaded_documents.c.status,
                uploaded_documents.c.uploaded_at,
            ).order_by(uploaded_documents.c.uploaded_at.desc())
        ).mappings().all()
    return [dict(row) for row in rows]


def close_database() -> None:
    engine.dispose()


__all__ = [
    "SQLAlchemyError",
    "close_database",
    "initialize_database",
    "list_documents",
    "save_document",
    "set_document_status",
]
