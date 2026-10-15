import uuid

import pytest
from sqlalchemy import select

from app.models import ChatMessage, ChatSession, User
from app.services import chat as chat_service


class FakeHit:
    def __init__(self, chunk_id, document_id, filename, content, score):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.filename = filename
        self.content = content
        self.score = score


@pytest.mark.asyncio
async def test_send_message_refuses_when_no_context(db_session, test_user, monkeypatch) -> None:
    async def fake_search_chunks(**kwargs):
        return []

    monkeypatch.setattr(chat_service, "search_chunks", fake_search_chunks)

    chat_session, answer, sources = await chat_service.send_message(
        session=db_session, user_id=test_user.id, message="anything", session_id=None
    )

    assert answer == chat_service.NO_CONTEXT_ANSWER
    assert sources == []

    messages = (
        await db_session.scalars(select(ChatMessage).where(ChatMessage.session_id == chat_session.id))
    ).all()
    assert len(messages) == 2  # user + assistant, no LLM call made


@pytest.mark.asyncio
async def test_send_message_generates_grounded_answer(db_session, test_user, monkeypatch) -> None:
    hit = FakeHit(uuid.uuid4(), uuid.uuid4(), "doc.pdf", "relevant content", 0.9)

    async def fake_search_chunks(**kwargs):
        return [hit]

    async def fake_generate(messages):
        assert "relevant content" in messages[1]["content"]
        return "Here is your answer [1]."

    monkeypatch.setattr(chat_service, "search_chunks", fake_search_chunks)
    monkeypatch.setattr(chat_service, "generate_chat_response", fake_generate)

    _, answer, sources = await chat_service.send_message(
        session=db_session, user_id=test_user.id, message="a question", session_id=None
    )

    assert answer == "Here is your answer [1]."
    assert len(sources) == 1
    assert sources[0].filename == "doc.pdf"


@pytest.mark.asyncio
async def test_send_message_reuses_existing_session(db_session, test_user, monkeypatch) -> None:
    async def fake_search_chunks(**kwargs):
        return []

    monkeypatch.setattr(chat_service, "search_chunks", fake_search_chunks)

    first, _, _ = await chat_service.send_message(
        session=db_session, user_id=test_user.id, message="first", session_id=None
    )
    second, _, _ = await chat_service.send_message(
        session=db_session, user_id=test_user.id, message="second", session_id=first.id
    )

    assert first.id == second.id


@pytest.mark.asyncio
async def test_send_message_ignores_foreign_session_id(db_session, test_user, monkeypatch) -> None:
    """A session_id from another user must not be reused or leak history."""
    other = User(email=f"other_{uuid.uuid4()}@example.com", hashed_password="x")
    db_session.add(other)
    await db_session.flush()

    foreign_session = ChatSession(user_id=other.id)
    db_session.add(foreign_session)
    await db_session.flush()

    async def fake_search_chunks(**kwargs):
        return []

    monkeypatch.setattr(chat_service, "search_chunks", fake_search_chunks)

    chat_session, _, _ = await chat_service.send_message(
        session=db_session, user_id=test_user.id, message="hi", session_id=foreign_session.id
    )

    assert chat_session.id != foreign_session.id