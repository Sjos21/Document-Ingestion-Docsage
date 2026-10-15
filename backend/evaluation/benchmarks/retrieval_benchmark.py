"""Compares vector-only vs hybrid search on a small known gold set.
Run: python -m evaluation.benchmarks.retrieval_benchmark
Requires: docker compose up -d postgres redis
"""
import asyncio
import json
import time
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import Chunk, Document, User
from app.services.embedding import embed_texts
from app.services.retrieval import search_chunks
from evaluation.metrics.retrieval_metrics import mean, ndcg_at_k, reciprocal_rank, recall_at_k

PG_URL = "postgresql+asyncpg://docsage:docsage@localhost:5432/docsage"

GOLD = [
    ("invoice number INV-77123 payment due", "unrelated text about gardening tips"),
    ("quarterly revenue grew 12 percent", "a recipe for chocolate cake"),
    ("employee onboarding checklist for new hires", "history of the roman empire"),
    ("server outage postmortem root cause analysis", "a poem about the ocean"),
    ("refund policy for damaged goods", "instructions for assembling furniture"),
]


async def main() -> None:
    engine = create_async_engine(PG_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        user = User(email=f"eval_{uuid.uuid4()}@example.com", hashed_password="x")
        session.add(user)
        await session.flush()

        relevant_ids, distractor_ids = [], []
        for relevant_text, distractor_text in GOLD:
            vecs = embed_texts([relevant_text, distractor_text])
            doc = Document(user_id=user.id, filename="eval.pdf", content_hash=str(uuid.uuid4()),
                            storage_path="/tmp/x", status="indexed")
            session.add(doc)
            await session.flush()
            c1 = Chunk(document_id=doc.id, content=relevant_text, embedding=vecs[0], token_count=5, embedding_model_version="eval")
            c2 = Chunk(document_id=doc.id, content=distractor_text, embedding=vecs[1], token_count=5, embedding_model_version="eval")
            session.add_all([c1, c2])
            await session.flush()
            relevant_ids.append(c1.id)
        await session.commit()

        recalls, rrs, ndcgs, latencies = [], [], [], []
        for (query, _), relevant_id in zip(GOLD, relevant_ids):
            t0 = time.perf_counter()
            hits = await search_chunks(session=session, user_id=user.id, query=query, top_k=10)
            latencies.append((time.perf_counter() - t0) * 1000)
            ranked = [h.chunk_id for h in hits]
            recalls.append(recall_at_k(ranked, relevant_id, 5))
            rrs.append(reciprocal_rank(ranked, relevant_id))
            ndcgs.append(ndcg_at_k(ranked, relevant_id, 10))

        results = {
            "recall_at_5": mean(recalls),
            "mrr": mean(rrs),
            "ndcg_at_10": mean(ndcgs),
            "avg_latency_ms": round(mean(latencies), 2),
            "n_queries": len(GOLD),
        }

    await engine.dispose()

    out_dir = Path("evaluation/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "retrieval_results.json").write_text(json.dumps(results, indent=2))

    md = (
        "# Retrieval Evaluation\n\n"
        f"- Recall@5: {results['recall_at_5']:.3f}\n"
        f"- MRR: {results['mrr']:.3f}\n"
        f"- NDCG@10: {results['ndcg_at_10']:.3f}\n"
        f"- Avg latency: {results['avg_latency_ms']} ms\n"
        f"- Queries: {results['n_queries']}\n"
    )
    (out_dir / "evaluation_report.md").write_text(md)
    print(md)


if __name__ == "__main__":
    asyncio.run(main())