import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.security import (
    create_access_token,
    ensure_utc,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expires_at,
    verify_password,
)
from app.models import RefreshToken, User
from app.schemas.auth import TokenResponse, UserResponse


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    async def register(self, email: str, password: str) -> tuple[UserResponse, TokenResponse]:
        existing = await self._session.scalar(select(User).where(User.email == email))
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(email=email, hashed_password=hash_password(password))
        self._session.add(user)
        await self._session.flush()

        tokens = await self._issue_tokens(user.id)
        await self._session.commit()
        await self._session.refresh(user)

        return self._user_response(user), tokens

    async def login(self, email: str, password: str) -> tuple[UserResponse, TokenResponse]:
        user = await self._session.scalar(select(User).where(User.email == email))
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        tokens = await self._issue_tokens(user.id)
        await self._session.commit()

        return self._user_response(user), tokens

    async def refresh(self, raw_refresh_token: str) -> TokenResponse:
        token_hash = hash_refresh_token(raw_refresh_token)
        token = await self._session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )

        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        now = datetime.now(UTC)
        if ensure_utc(token.expires_at) <= now:
            token.revoked = True
            await self._session.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        if token.revoked:
            await self._revoke_token_descendants(token.replaced_by_id)
            await self._session.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token reuse detected",
            )

        new_tokens = await self._rotate_refresh_token(token)
        await self._session.commit()
        return new_tokens

    async def logout(self, raw_refresh_token: str) -> None:
        token_hash = hash_refresh_token(raw_refresh_token)
        token = await self._session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        if token is not None and not token.revoked:
            token.revoked = True
            await self._session.commit()

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        user = await self._session.get(User, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user

    async def _issue_tokens(self, user_id: uuid.UUID) -> TokenResponse:
        access_token = create_access_token(user_id=user_id, settings=self._settings)
        raw_refresh = generate_refresh_token()
        refresh_record = RefreshToken(
            user_id=user_id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=refresh_token_expires_at(self._settings),
        )
        self._session.add(refresh_record)
        await self._session.flush()

        return TokenResponse(access_token=access_token, refresh_token=raw_refresh)

    async def _rotate_refresh_token(self, current: RefreshToken) -> TokenResponse:
        raw_refresh = generate_refresh_token()
        new_record = RefreshToken(
            user_id=current.user_id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=refresh_token_expires_at(self._settings),
        )
        self._session.add(new_record)
        await self._session.flush()

        current.revoked = True
        current.replaced_by_id = new_record.id

        access_token = create_access_token(user_id=current.user_id, settings=self._settings)
        return TokenResponse(access_token=access_token, refresh_token=raw_refresh)

    async def _revoke_token_descendants(self, token_id: uuid.UUID | None) -> None:
        """Revoke a rotated token chain from the replacement onward."""
        current_id = token_id
        while current_id is not None:
            await self._session.execute(
                update(RefreshToken)
                .where(RefreshToken.id == current_id)
                .values(revoked=True)
            )
            next_id = await self._session.scalar(
                select(RefreshToken.replaced_by_id).where(RefreshToken.id == current_id)
            )
            current_id = next_id

    @staticmethod
    def _user_response(user: User) -> UserResponse:
        return UserResponse(
            id=str(user.id),
            email=user.email,
            created_at=user.created_at.isoformat(),
        )