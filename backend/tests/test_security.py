import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from jose import jwt

from app.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    hashed = hash_password("secure-password")
    assert hashed != "secure-password"
    assert verify_password("secure-password", hashed)
    assert not verify_password("wrong-password", hashed)


def test_refresh_token_hash_is_deterministic() -> None:
    token = "sample-refresh-token"
    assert hash_refresh_token(token) == hash_refresh_token(token)
    assert len(hash_refresh_token(token)) == 64


def test_generate_refresh_token_unique() -> None:
    tokens = {generate_refresh_token() for _ in range(10)}
    assert len(tokens) == 10


def test_create_and_decode_access_token(test_settings: Settings) -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, settings=test_settings)
    assert decode_access_token(token, test_settings) == user_id


def test_decode_access_token_rejects_wrong_type(test_settings: Settings) -> None:
    payload = {
        "sub": str(uuid.uuid4()),
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "type": "refresh",
    }
    token = jwt.encode(payload, test_settings.jwt_secret_key, algorithm=test_settings.jwt_algorithm)
    with pytest.raises(ValueError, match="Invalid token type"):
        decode_access_token(token, test_settings)


def test_decode_access_token_rejects_invalid_signature(test_settings: Settings) -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, settings=test_settings)
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises(ValueError, match="Invalid access token"):
        decode_access_token(tampered, test_settings)
