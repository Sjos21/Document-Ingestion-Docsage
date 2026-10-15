"""Manual smoke test: real upload -> real indexing -> real chat via Ollama.

Requires: docker compose up -d postgres redis, arq worker running,
uvicorn running, and `ollama serve` with the configured model pulled.
Run: python scripts/smoke_test_chat.py
"""
import asyncio
import time

import httpx

BASE = "http://localhost:8000/api/v1"
FIXTURE = "tests/fixtures/sample.pdf"


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE, timeout=120) as client:
        email = f"chatsmoke_{int(time.time())}@example.com"
        register = await client.post("/auth/register", json={"email": email, "password": "password123"})
        register.raise_for_status()
        headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

        with open(FIXTURE, "rb") as f:
            upload = await client.post(
                "/documents/upload", headers=headers, files={"file": ("sample.pdf", f, "application/pdf")}
            )
        upload.raise_for_status()
        doc_id = upload.json()["id"]

        for _ in range(30):
            status = (await client.get(f"/documents/{doc_id}", headers=headers)).json()["status"]
            if status in ("indexed", "failed"):
                break
            await asyncio.sleep(1)
        print(f"document status: {status}")

        chat_resp = await client.post("/chat", headers=headers, json={"message": "What is this document about?"})
        chat_resp.raise_for_status()
        body = chat_resp.json()
        print(f"answer: {body['answer']}")
        print(f"sources: {len(body['sources'])} chunk(s) cited")

        if body["sources"]:
            print("PASS: chat answered with grounded sources.")
        else:
            print("WARN: no sources returned -- check retrieval/indexing.")


if __name__ == "__main__":
    asyncio.run(main())