"""Measures embedding + search latency in isolation, N iterations.
Run: python -m evaluation.benchmarks.latency_benchmark
"""
import asyncio
import json
import time
from pathlib import Path

from app.services.embedding import embed_texts

N = 10


async def main() -> None:
    embed_times = []
    for _ in range(N):
        t0 = time.perf_counter()
        embed_texts(["sample query text for latency measurement"])
        embed_times.append((time.perf_counter() - t0) * 1000)

    results = {
        "embedding_avg_ms": round(sum(embed_times) / N, 2),
        "embedding_p95_ms": round(sorted(embed_times)[int(N * 0.95) - 1], 2),
        "iterations": N,
    }
    out_dir = Path("evaluation/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latency_results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())