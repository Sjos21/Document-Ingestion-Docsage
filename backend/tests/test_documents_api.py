"""HTTP-level tests for /documents endpoints, incl. multi-tenant isolation."""
import os

import pytest
from httpx import AsyncClient

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample.pdf")
AUTH = "/api/v1/auth"
DOCS = "/api/v1/documents"


async def _register(client: AsyncClient, email: str, password: str = "password123") -> dict:
    response = await client.post(AUTH + "/register", json={"email": email, "password": password})
    assert response.status_code == 201
    return response.json()


def _auth_header(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.mark.asyncio
async def test_upload_returns_201_and_uploaded_status(client: AsyncClient) -> None:
    tokens = await _register(client, "upload@example.com")
    with open(FIXTURE, "rb") as f:
        response = await client.post(
            f"{DOCS}/upload",
            headers=_auth_header(tokens),
            files={"file": ("sample.pdf", f, "application/pdf")},
        )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "sample.pdf"
    assert body["status"] == "uploaded"


@pytest.mark.asyncio
async def test_upload_requires_authentication(client: AsyncClient) -> None:
    with open(FIXTURE, "rb") as f:
        response = await client.post(
            f"{DOCS}/upload", files={"file": ("sample.pdf", f, "application/pdf")}
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_returns_only_own_documents(client: AsyncClient) -> None:
    tokens_a = await _register(client, "lista@example.com")
    tokens_b = await _register(client, "listb@example.com")

    with open(FIXTURE, "rb") as f:
        await client.post(
            f"{DOCS}/upload",
            headers=_auth_header(tokens_a),
            files={"file": ("a.pdf", f, "application/pdf")},
        )

    response_a = await client.get(DOCS, headers=_auth_header(tokens_a))
    response_b = await client.get(DOCS, headers=_auth_header(tokens_b))

    assert response_a.status_code == 200
    assert response_b.status_code == 200
    assert response_a.json()["total"] == 1
    assert response_b.json()["total"] == 0


@pytest.mark.asyncio
async def test_get_document_cross_user_returns_404(client: AsyncClient) -> None:
    tokens_a = await _register(client, "geta@example.com")
    tokens_b = await _register(client, "getb@example.com")

    with open(FIXTURE, "rb") as f:
        upload_resp = await client.post(
            f"{DOCS}/upload",
            headers=_auth_header(tokens_a),
            files={"file": ("a.pdf", f, "application/pdf")},
        )
    doc_id = upload_resp.json()["id"]

    own_response = await client.get(f"{DOCS}/{doc_id}", headers=_auth_header(tokens_a))
    other_response = await client.get(f"{DOCS}/{doc_id}", headers=_auth_header(tokens_b))

    assert own_response.status_code == 200
    assert other_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_cross_user_returns_404_and_does_not_delete(
    client: AsyncClient,
) -> None:
    tokens_a = await _register(client, "dela@example.com")
    tokens_b = await _register(client, "delb@example.com")

    with open(FIXTURE, "rb") as f:
        upload_resp = await client.post(
            f"{DOCS}/upload",
            headers=_auth_header(tokens_a),
            files={"file": ("a.pdf", f, "application/pdf")},
        )
    doc_id = upload_resp.json()["id"]

    forbidden_delete = await client.delete(f"{DOCS}/{doc_id}", headers=_auth_header(tokens_b))
    assert forbidden_delete.status_code == 404

    still_there = await client.get(f"{DOCS}/{doc_id}", headers=_auth_header(tokens_a))
    assert still_there.status_code == 200

    own_delete = await client.delete(f"{DOCS}/{doc_id}", headers=_auth_header(tokens_a))
    assert own_delete.status_code == 200

    gone = await client.get(f"{DOCS}/{doc_id}", headers=_auth_header(tokens_a))
    assert gone.status_code == 404

@pytest.mark.asyncio
async def test_upload_rejects_file_over_size_limit(client: AsyncClient, test_settings) -> None:
    tokens = await _register(client, "toobig@example.com")
    test_settings.max_upload_mb = 0  # mutate the actual instance the app dependency-overrides to

    with open(FIXTURE, "rb") as f:
        response = await client.post(
            f"{DOCS}/upload",
            headers=_auth_header(tokens),
            files={"file": ("sample.pdf", f, "application/pdf")},
        )

    assert response.status_code == 413



@pytest.mark.asyncio
async def test_upload_records_audit_event(client: AsyncClient) -> None:
    from sqlalchemy import select

    from app.models import SystemEvent

    tokens = await _register(client, "audit_upload@example.com")
    with open(FIXTURE, "rb") as f:
        await client.post(
            f"{DOCS}/upload", headers=_auth_header(tokens), files={"file": ("a.pdf", f, "application/pdf")}
        )

    # NOTE: uses the same in-memory SQLite session as the app via dependency
    # override, so this reads back what the route just committed.
    from app.db.session import get_db_session
    session_gen = client._transport.app.dependency_overrides[get_db_session]()
    session = await session_gen.__anext__()
    row = await session.scalar(select(SystemEvent).where(SystemEvent.event_type == "UPLOAD_COMPLETED"))
    assert row is not None
    assert row.status == "new"
