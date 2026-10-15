# Master Build Prompt — Local RAG Document Search Platform

Paste this in full as the first message in a new Cursor chat (or save as `docs/architecture.md` in the repo root and reference it in every subsequent prompt with `@architecture.md`). Do not ask Cursor to build the whole system in one shot — work phase by phase as instructed at the bottom.

---

## Project

A production-grade, single-user-first, locally-deployed RAG document search platform. Users upload documents (PDF first, DOCX/images later), the system extracts/chunks/embeds them, and supports hybrid semantic+keyword search with LLM-synthesized answers citing source chunks. Fully local inference (Ollama) — no paid APIs, no cloud dependency required to run.

## Non-negotiable architectural decisions — do not deviate without asking

- **Single database**: PostgreSQL 16 + `pgvector` extension. Do NOT introduce a separate vector DB (no Chroma/Qdrant/Weaviate/Pinecone). Relational data and embeddings live in the same Postgres instance.
- **Hybrid retrieval**: BM25 via Postgres native full-text search (`tsvector`/`ts_rank`) + vector search via `pgvector`, fused with **Reciprocal Rank Fusion (RRF)** — not weighted score averaging. BM25 and cosine similarity are different scales; never blend raw scores directly.
- **Reranking**: cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) on top ~20-30 fused candidates, reduced to top 5 before LLM generation. Do not rerank more than ~30 candidates — unnecessary CPU cost.
- **LLM**: Ollama only, local, CPU-inference. Default model `llama3.2:3b` or `phi3:mini` — do not default to a larger model without confirming hardware can handle the latency. Stream responses token-by-token to the frontend; do not block on full generation before returning anything to the client.
- **Auth**: JWT access + refresh tokens. Refresh tokens stored **hashed** in the DB with **rotation and reuse detection** (not stateless JWT with no revocation path). Passwords hashed with bcrypt via `passlib`.
- **Multi-tenant isolation**: every single document/chunk/query/analytics query MUST filter by `user_id`. Treat a missing `user_id` filter as a security bug, not a style issue. Write a test that explicitly asserts user A cannot retrieve user B's documents or chunks via any endpoint.
- **Storage abstraction**: implement a `StorageBackend` interface (`save`, `load`, `delete`) with a `LocalStorage` implementation now. All file I/O in the app goes through this interface — no direct `open()`/`os` calls scattered in business logic. This is so S3/Azure/GCS backends can be added later with zero changes outside the storage module.
- **Idempotent ingestion**: re-processing an unchanged file must be a no-op. Dedupe/change-detection by **content hash (SHA-256)**, not file modification time (mtime is unreliable across copy/move operations).
- **Background jobs**: Redis + `arq` for async ingestion/embedding jobs. Do not use Celery — unjustified operational overhead at this scale.
- **Observability now**: structured logging via `structlog` (JSON output) + a request-ID middleware propagated through async calls, and a `query_logs` Postgres table (query text, latency breakdown by stage, retrieval scores, token counts, user_id, timestamp).
- **Observability deferred**: no Prometheus/OpenTelemetry/Grafana in this build. Flag it as a documented future improvement in the README instead of implementing it.

## Tech stack

**Backend**: Python, FastAPI, SQLAlchemy (async) + Alembic migrations, Pydantic v2, `passlib`/`python-jose` for auth, `sentence-transformers` (`all-MiniLM-L6-v2`) for embeddings, `pytesseract` for OCR, `pdfplumber`/`PyMuPDF` for PDF extraction, `arq` for jobs, `structlog` for logging, `pytest` + `pytest-asyncio` for tests.

**Frontend**: React + TypeScript, Tailwind CSS, shadcn/ui components, `recharts` for analytics dashboard, React Query for API state, streaming fetch/EventSource for LLM token streaming.

**Infra**: Docker multi-stage builds, `docker-compose.yml` (services: `api`, `frontend`, `postgres`, `redis`, `worker`), GitHub Actions CI (lint → type-check → test → build images), no cloud deploy target for now — repo lives on GitHub, runs via `docker compose up` locally.

## Data model (implement via SQLAlchemy models + Alembic migrations)

```
users            (id, email UNIQUE, hashed_password, created_at)
refresh_tokens   (id, user_id FK, token_hash, expires_at, revoked BOOL, replaced_by_id)
documents        (id, user_id FK, filename, content_hash UNIQUE per user, storage_path, status, indexed_at, created_at)
chunks           (id, document_id FK, content TEXT, embedding VECTOR(384), token_count, ocr_confidence NULLABLE, tsv TSVECTOR)
query_logs       (id, user_id FK, query_text, latency_embed_ms, latency_rerank_ms, latency_llm_ms, result_count, created_at)
chat_sessions    (id, user_id FK, created_at)
chat_messages    (id, session_id FK, role, content, retrieved_chunk_ids ARRAY, created_at)
```

## Retrieval pipeline (implement exactly in this order)

```
Query
 ├─ BM25 candidates (Postgres tsvector/ts_rank)
 └─ Vector candidates (pgvector cosine similarity)
       ↓
   RRF fusion → top 20-30 combined candidates
       ↓
   Cross-encoder rerank → top 5
       ↓
   Ollama generation (streamed), prompted to answer ONLY from
   provided chunks and explicitly say "not found in your documents"
   if retrieval is insufficient — never answer from parametric knowledge
       ↓
   Response includes cited chunk_ids for traceability
```

## Testing requirements (do not skip)

- ≥80% coverage on: auth logic, ingestion idempotency, RRF fusion math, multi-tenant isolation.
- Explicit test: two users, assert zero cross-user data leakage across every document/search/analytics endpoint.
- Explicit test: refresh token reuse after rotation is rejected and triggers revocation of the token family.
- Explicit test: re-ingesting an unchanged file produces zero new embedding calls.
- Eval harness (`eval/` module, separate from unit tests): a fixed set of test questions with expected source document/chunk, tracked in git. Compute Recall@5, MRR, and latency. This should be runnable as a script and eventually wired into CI as a regression gate on retrieval quality.

## Known failure modes to design around explicitly, not discover later

1. Concurrent query during re-indexing of the same document — don't let searches hit a half-embedded document; use a status flag (`indexed`/`indexing`/`stale`) on `documents` and filter search to `indexed` only.
2. File deletion/move — must remove or orphan-flag associated chunks, not leave dead vectors searchable.
3. Corrupt/unparseable file during batch ingestion must not kill the whole job — per-file try/except with dead-letter logging into `documents.status = 'failed'` plus an error reason field.
4. Large file upload abuse — enforce size limits at the API layer before any processing starts.
5. Ollama unavailable/model not pulled — fail with a clear error message, not a silent hang; add a startup health check that verifies the configured model is available.

## Build order — work phase by phase, do NOT attempt all phases in one prompt

1. **Phase 0**: Repo scaffold — monorepo layout, `docker-compose.yml`, Postgres+pgvector service, Alembic setup, storage interface + `LocalStorage`, config via `pydantic-settings`, CI skeleton (lint+typecheck+test on push, no deploy step yet).
2. **Phase 1**: Auth — users, JWT access+refresh with rotation/reuse detection, protected route dependency, full test coverage.
3. **Phase 2**: Ingestion — upload endpoint → extract (PDF first) → chunk → embed → store, idempotent via content hash, async via `arq`.
4. **Phase 3**: Retrieval — BM25 + vector + RRF fusion, tested against a small (~20 question) eval set.
5. **Phase 4**: Reranking + Ollama streamed generation with chunk citations.
6. **Phase 5**: Analytics — `query_logs` writes, dashboard API + frontend charts.
7. **Phase 6**: Full eval harness (200 questions), wire as a CI check that fails on retrieval regression.
8. **Phase 7**: Frontend polish (shadcn/ui), README with architecture diagram and documented trade-offs (why Postgres+pgvector over a dedicated vector DB, why local-only LLM and its latency implications, what's deferred — Prometheus/OTel, cloud storage backends, multi-model support).

**Instruction to Cursor**: Confirm understanding of this architecture, then wait for me to say "start Phase 0" before generating any code. After each phase, stop and wait for review before proceeding to the next phase. Flag any point where you deviate from a decision listed above, and state why, rather than silently choosing a different approach.
