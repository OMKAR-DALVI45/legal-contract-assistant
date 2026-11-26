# Legal Contract Assistant

Upload text-based contract PDFs, extract and index their text in ChromaDB, then ask questions in a chat interface. PostgreSQL stores the uploaded PDF and document status. Answers include document and page references and are grounded in retrieved excerpts.

> This tool analyzes documents and is not legal advice. Retrieved contract excerpts are sent to Groq to generate answers.

## Project structure

```text
app/
  main.py       FastAPI routes and startup point
  database.py   PostgreSQL storage for uploaded PDFs and status
  rag.py        PDF extraction, chunking, ChromaDB indexing, retrieval, and answers
  schemas.py    Chat request and response schemas
static/         Browser upload and chat interface
data/chroma/    Local ChromaDB data (ignored by Git)
```

## Setup

1. Create a PostgreSQL database and copy `.env.example` to `.env`.
2. Set `DATABASE_URL` in `.env` to your PostgreSQL connection string. For this project use the `postgresql+pg8000://...` format.
3. Set `GROQ_API_KEY` in `.env`. The default answer model is `openai/gpt-oss-120b`; change it with `GROQ_MODEL` if needed.
4. Install dependencies: `pip install -r requirements.txt`.
5. Start the app from this folder: `uvicorn app.main:app --reload`.
6. Open `http://127.0.0.1:8000`, upload a PDF, wait until its status is `ready`, and ask a question.

The database user needs permission to create and write tables. Uploads are limited to 20 MB. ChromaDB persists its local index under `data/chroma/`. The first indexing run may download ChromaDB's default embedding model. Scanned PDFs without selectable text need OCR before upload.
