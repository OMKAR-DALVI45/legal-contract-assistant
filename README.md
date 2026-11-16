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

## Status
In progress. Started November 2026.