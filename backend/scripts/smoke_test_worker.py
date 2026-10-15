"""Manual smoke test: real upload -> real arq worker -> real Postgres."""
import asyncio
import time

import httpx

BASE = "http://localhost:8000/api/v1"
FIXTURE = "tests/fixtures/sample.pdf"


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as client:
        email = f"smoke_{int(time.time())}@example.com"
        register = await client.post("/auth/register", json={"email": email, "password": "password123"})
        register.raise_for_status()
        token = register.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        with open(FIXTURE, "rb") as f:
            upload = await client.post(
                "/documents/upload", headers=headers, files={"file": ("sample.pdf", f, "application/pdf")}
            )
        upload.raise_for_status()
        doc_id = upload.json()["id"]
        print(f"uploaded document {doc_id}, polling for worker to process...")

        for attempt in range(30):
            resp = await client.get(f"/documents/{doc_id}", headers=headers)
            status = resp.json()["status"]
            print(f"  [{attempt}] status={status}")
            if status in ("indexed", "failed"):
                break
            await asyncio.sleep(1)

        final = resp.json()
        if final["status"] == "indexed":
            print("PASS: worker processed document end-to-end via real Redis/arq.")
        else:
            print(f"FAIL: status={final['status']} reason={final.get('status_reason')}")
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())