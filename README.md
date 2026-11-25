# legal-contract-assistant
RAG-based AI assistant for contract analysis: clause-aware chunking, hybrid search, cited answers, risk flags and version comparison. Built with FastAPI, LangGraph, PostgreSQL, Redis and Qdrant.
<br>
# Legal Contract Assistant

An AI assistant that helps people understand contracts. You upload a contract, ask questions in plain language, and get answers with exact clause citations. If the answer is not in the document, it says so instead of guessing.

> This tool analyzes documents and is not legal advice.

## Planned features
- Clause-aware PDF parsing and chunking
- Question answering with section and page citations
- Hybrid search with reranking, measured with an evaluation set
- Clause extraction and risk flags
- Version comparison

## Tech stack
Python, FastAPI, PostgreSQL, Redis, Qdrant, LangChain, LangGraph, Streamlit

## Run the upload app

The upload endpoint stores each PDF's bytes and metadata in the PostgreSQL table `uploaded_documents`. The table is created automatically when the app starts. The document list is loaded from PostgreSQL, so it survives app restarts.

1. Install dependencies with `pip install -r requirements.txt`.
2. Set `DATABASE_URL` in `.env` to your PostgreSQL connection string. This project is configured to use the `pg8000` driver (`postgresql+pg8000://...`).
3. Start the app with `uvicorn main:app --reload` from this folder.

The database user must be able to create and write tables in the selected schema. Uploaded PDFs are limited to 20 MB.

## Status
In progress. Started November 2026.
