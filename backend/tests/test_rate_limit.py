import uuid

import pytest
from fastapi import HTTPException

from app.services.rate_limit import enforce_rate_limit


@pytest.mark.asyncio
async def test_rate_limit_blocks_after_threshold() -> None:
    user_id = uuid.uuid4()
    for _ in range(3):
        await enforce_rate_limit(user_id=user_id, action="test_action", limit=3, window_seconds=60)

    with pytest.raises(HTTPException) as exc_info:
        await enforce_rate_limit(user_id=user_id, action="test_action", limit=3, window_seconds=60)
    assert exc_info.value.status_code == 429