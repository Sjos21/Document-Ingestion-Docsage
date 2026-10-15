from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep, CurrentUser
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, auth_service: AuthServiceDep) -> TokenResponse:
    _, tokens = await auth_service.register(body.email, body.password)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, auth_service: AuthServiceDep) -> TokenResponse:
    _, tokens = await auth_service.login(body.email, body.password)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, auth_service: AuthServiceDep) -> TokenResponse:
    return await auth_service.refresh(body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: LogoutRequest, auth_service: AuthServiceDep) -> None:
    await auth_service.logout(body.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser, auth_service: AuthServiceDep) -> UserResponse:
    return AuthService._user_response(current_user)
