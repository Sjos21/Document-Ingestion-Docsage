import uuid

import pytest
from sqlalchemy import select

from app.models import SystemEvent
from app.services.audit import record_event


@pytest.mark.asyncio
async def test_record_event_persists_row(db_session) -> None:
    user_id = uuid.uuid4()
    await record_event(
        db_session,
        event_type="TEST_EVENT",
        user_id=user_id,
        duration_ms=123.4,
        metadata={"key": "value"},
    )
    await db_session.commit()

    row = await db_session.scalar(select(SystemEvent).where(SystemEvent.event_type == "TEST_EVENT"))
    assert row is not None
    assert row.user_id == user_id
    assert row.duration_ms == 123.4
    assert row.event_metadata == {"key": "value"}


@pytest.mark.asyncio
async def test_record_event_does_not_raise_on_db_error(db_session, monkeypatch) -> None:
    async def broken_flush():
        raise RuntimeError("simulated DB failure")

    monkeypatch.setattr(db_session, "flush", broken_flush)

    # Must not raise -- audit failures are logged, never propagated to the caller.
    await record_event(db_session, event_type="TEST_EVENT_FAILS")