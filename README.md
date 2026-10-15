# DocSage

A local-first, production-grade RAG (Retrieval-Augmented Generation) document search and chat platform. Upload PDFs, ask questions, get answers grounded in your own documents — with full transparency into how each answer was retrieved and generated.

Built as a hands-on systems project to demonstrate real backend/AI engineering: authentication, async ingestion pipelines, hybrid search, LLM orchestration, and observability — not just a LangChain wrapper.

## What it does

1. **Upload a PDF** → extracted, chunked, embedded, and indexed asynchronously.
2. **Ask a question** → hybrid search (vector + keyword) retrieves the most relevant chunks, a cross-encoder reranks them, and a local LLM (Ollama) generates a grounded answer — citing sources, refusing to answer if nothing relevant is found.
3. **See everything** → live pipeline status during upload, and a transparency panel showing exactly which chunks were retrieved, how (vector/BM25 scores), and how long each stage took.

## Architecture

```
Auth (JWT) → Document Ingestion → Extraction → Chunking → Embedding → pgvector
                                                                            │
Query → Vector Search ─┐                                                  │
                        ├─→ RRF Fusion → Cross-Encoder Rerank → LLM (Ollama) → Answer + Citations
Query → BM25 Search ────┘
```

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI, async SQLAlchemy | Async-native, auto docs, type-safe |
| Database | PostgreSQL 16 + pgvector | Single DB for relational + vector data — no separate vector store |
| Search | Native Postgres full-text (BM25) + pgvector cosine similarity, fused via Reciprocal Rank Fusion | Avoids a 3rd datastore; RRF avoids score-normalization problems |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Small model, keeps local CPU latency low |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | 384-dim, local, CPU-only |
| LLM | Ollama (`llama3.2:3b`), local, streamed | Fully offline, no API costs |
| Auth | JWT access + refresh tokens, rotation + reuse detection | Standard, revocable, no 3rd-party auth dependency |
| Background jobs | Redis + arq | Async document processing without blocking uploads |
| Frontend | React + Vite + Tailwind + shadcn/ui | Minimal, fast, matches Vercel/Linear-style aesthetic |
| Observability | structlog (JSON logs) + `system_events` audit table | Correlatable via `request_id` across API and worker |
| CI/CD | GitHub Actions (lint → typecheck → test → build) | Standard pipeline |

## Project phases (build log)

- **Phase 0** — Repo scaffold, Docker Compose, storage abstraction, DB + pgvector, structured logging, CI skeleton
- **Phase 1** — Auth: JWT rotation, refresh-token reuse detection, multi-tenant isolation
- **Phase 2** — Ingestion: upload → extract → chunk → embed → index, idempotent, async via arq
- **Phase 3** — Vector search endpoint
- **Phase 4** — Hybrid search (BM25 + vector + RRF) + cross-encoder reranking
- **Phase 5** — LLM generation via Ollama, streamed, grounded, citation-aware
- **Phase 6** — Audit logging: `system_events` table, request-ID correlation across API/worker
- **Phase 7** — Retrieval evaluation harness (Recall@5, MRR, latency)
- **Phase 8** *(in progress)* — Frontend: live pipeline visualization, chat UI, transparency panel, analytics dashboard

## Key design decisions

- **Single database (Postgres + pgvector)** over a dedicated vector DB — fewer moving parts, transactional consistency between chunks and their metadata.
- **RRF, not weighted score blending** — BM25 and cosine similarity scores are on incompatible scales; fusing by rank position avoids the normalization problem entirely.
- **Local-only LLM** — no API costs, fully offline-capable, at the cost of higher latency than a hosted model (mitigated via token streaming).
- **Idempotent ingestion** — re-uploading an unchanged file is a no-op (content-hash based), not a re-embed.
- **Audit trail is best-effort** — a logging failure never fails the actual request it's describing.

## Running locally

Requires: Docker Desktop, Python 3.12, Node.js, [Ollama](https://ollama.com).

```powershell
# 1. Pull the LLM model (one-time)
ollama pull llama3.2:3b

# 2. Start infra
docker compose up -d postgres redis

# 3. Start Ollama
ollama serve

# 4. Backend
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# 5. Background worker
cd backend
python -m arq app.worker.WorkerSettings

# 6. Frontend
cd frontend
npm install
npm run dev
```

API docs available at `http://localhost:8000/docs` once running.

## Testing

```powershell
cd backend
pytest tests\ -v
```

56+ tests covering: auth flows and token security, ingestion idempotency and failure handling, multi-tenant isolation at every endpoint, hybrid search correctness against real Postgres, and RRF fusion logic.
