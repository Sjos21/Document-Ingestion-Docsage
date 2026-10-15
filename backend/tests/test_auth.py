import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_refresh_token
from app.models import RefreshToken

AUTH = "/api/v1/auth"


async def _register(client: AsyncClient, email: str, password: str = "password123") -> dict:
    response = await client.post(
        f"{AUTH}/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient) -> None:
    tokens = await _register(client, "alice@example.com")
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    response = await client.post(
        f"{AUTH}/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    await _register(client, "dup@example.com")
    response = await client.post(
        f"{AUTH}/register",
        json={"email": "dup@example.com", "password": "password123"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_password_too_short(client: AsyncClient) -> None:
    response = await client.post(
        f"{AUTH}/register",
        json={"email": "short@example.com", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient) -> None:
    await _register(client, "bob@example.com")
    response = await client.post(
        f"{AUTH}/login",
        json={"email": "bob@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get(f"{AUTH}/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(client: AsyncClient) -> None:
    tokens = await _register(client, "carol@example.com")
    response = await client.get(
        f"{AUTH}/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "carol@example.com"
    assert "id" in payload
    assert "created_at" in payload


@pytest.mark.asyncio
async def test_refresh_rotates_token(client: AsyncClient) -> None:
    tokens = await _register(client, "dave@example.com")
    original_refresh = tokens["refresh_token"]

    response = await client.post(
        f"{AUTH}/refresh",
        json={"refresh_token": original_refresh},
    )
    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["refresh_token"] != original_refresh
    assert new_tokens["access_token"] != tokens["access_token"]


@pytest.mark.asyncio
async def test_refresh_reuse_revokes_token_family(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tokens = await _register(client, "eve@example.com")
    refresh_v1 = tokens["refresh_token"]

    rotate_response = await client.post(
        f"{AUTH}/refresh",
        json={"refresh_token": refresh_v1},
    )
    assert rotate_response.status_code == 200
    refresh_v2 = rotate_response.json()["refresh_token"]

    reuse_response = await client.post(
        f"{AUTH}/refresh",
        json={"refresh_token": refresh_v1},
    )
    assert reuse_response.status_code == 401
    assert reuse_response.json()["detail"] == "Refresh token reuse detected"

    v2_hash = hash_refresh_token(refresh_v2)
    v2_record = await db_session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == v2_hash)
    )
    assert v2_record is not None
    assert v2_record.revoked is True

    v2_reuse_response = await client.post(
        f"{AUTH}/refresh",
        json={"refresh_token": refresh_v2},
    )
    assert v2_reuse_response.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tokens = await _register(client, "frank@example.com")
    refresh_token = tokens["refresh_token"]

    logout_response = await client.post(
        f"{AUTH}/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_response.status_code == 204

    token_hash = hash_refresh_token(refresh_token)
    record = await db_session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    assert record is not None
    assert record.revoked is True

    refresh_response = await client.post(
        f"{AUTH}/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_refresh_token(client: AsyncClient) -> None:
    response = await client.post(
        f"{AUTH}/refresh",
        json={"refresh_token": "not-a-valid-token"},
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_access_token_scoped_to_own_user(client: AsyncClient) -> None:
    tokens_a = await _register(client, "usera@example.com")
    tokens_b = await _register(client, "userb@example.com")

    response_a = await client.get(
        f"{AUTH}/me",
        headers={"Authorization": f"Bearer {tokens_a['access_token']}"},
    )
    response_b = await client.get(
        f"{AUTH}/me",
        headers={"Authorization": f"Bearer {tokens_b['access_token']}"},
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    email_a = response_a.json()["email"]
    email_b = response_b.json()["email"]

    assert email_a == "usera@example.com"
    assert email_b == "userb@example.com"
    assert email_a != email_b


@pytest.mark.asyncio
async def test_refresh_token_cannot_be_used_across_users(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tokens_a = await _register(client, "isoa@example.com")
    tokens_b = await _register(client, "isob@example.com")

    # B's refresh token must never rotate/return tokens tied to A's account,
    # regardless of which user is "currently" authenticated in a request.
    response = await client.post(
        f"{AUTH}/refresh",
        json={"refresh_token": tokens_b["refresh_token"]},
    )
    assert response.status_code == 200
    new_tokens = response.json()

    me_response = await client.get(
        f"{AUTH}/me",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "isob@example.com"
    assert me_response.json()["email"] != "isoa@example.com"

    # A's original tokens must remain valid and unaffected by B's refresh.
    me_a_response = await client.get(
        f"{AUTH}/me",
        headers={"Authorization": f"Bearer {tokens_a['access_token']}"},
    )
    assert me_a_response.status_code == 200
    assert me_a_response.json()["email"] == "isoa@example.com"