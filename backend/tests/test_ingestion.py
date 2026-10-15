import os
import uuid

import pytest
from sqlalchemy import select

from app.models import Chunk, Document, User
from app.services.ingestion import process_document, upload_document
from app.storage.local import LocalStorage

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample.pdf")



@pytest.fixture
def storage(tmp_path):
    return LocalStorage(tmp_path)


@pytest.mark.asyncio
async def test_upload_is_idempotent_on_same_content(db_session, test_user, storage) -> None:
    data = open(FIXTURE, "rb").read()

    doc1, is_new1 = await upload_document(
        session=db_session, storage=storage, user_id=test_user.id, filename="a.pdf", data=data
    )
    doc2, is_new2 = await upload_document(
        session=db_session, storage=storage, user_id=test_user.id, filename="a-renamed.pdf", data=data
    )

    assert is_new1 is True
    assert is_new2 is False
    assert doc1.id == doc2.id


@pytest.mark.asyncio
async def test_process_document_full_roundtrip(db_session, test_user, storage) -> None:
    data = open(FIXTURE, "rb").read()
    document, _ = await upload_document(
        session=db_session, storage=storage, user_id=test_user.id, filename="a.pdf", data=data
    )

    await process_document(session=db_session, storage=storage, document_id=document.id)

    refreshed = await db_session.get(Document, document.id)
    assert refreshed.status == "indexed"
    assert refreshed.indexed_at is not None

    chunks = (
        await db_session.scalars(select(Chunk).where(Chunk.document_id == document.id))
    ).all()
    assert len(chunks) > 0
    assert all(len(c.embedding) == 384 for c in chunks)


@pytest.mark.asyncio
async def test_process_document_corrupt_file_sets_failed(db_session, test_user, storage) -> None:
    document = Document(
        user_id=test_user.id,
        filename="bad.pdf",
        content_hash="deadbeef",
        storage_path=await storage.save(f"{test_user.id}/bad.pdf", b"not a pdf"),
        status="uploaded",
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    await process_document(session=db_session, storage=storage, document_id=document.id)

    refreshed = await db_session.get(Document, document.id)
    assert refreshed.status == "failed"
    assert refreshed.status_reason is not None


@pytest.mark.asyncio
async def test_document_isolation_between_users(db_session, storage) -> None:
    user_a = User(email="a@example.com", hashed_password="x")
    user_b = User(email="b@example.com", hashed_password="x")
    db_session.add_all([user_a, user_b])
    await db_session.commit()

    data = open(FIXTURE, "rb").read()
    doc_a, _ = await upload_document(
        session=db_session, storage=storage, user_id=user_a.id, filename="a.pdf", data=data
    )

    result = await db_session.scalars(select(Document).where(Document.user_id == user_b.id))
    assert list(result) == []

    result_a = await db_session.scalars(select(Document).where(Document.user_id == user_a.id))
    assert [d.id for d in result_a] == [doc_a.id]

