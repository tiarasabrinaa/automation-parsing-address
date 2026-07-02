from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
from app.schemas.auth import (
    AuthResponse,
    MessageResponse,
    PasswordChangeRequest,
    UserLoginRequest,
    UserPublic,
    UserRegisterRequest,
    UserUpdateRequest,
)
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth")
auth_service = AuthService()


@router.post("/register", response_model=AuthResponse)
async def register(payload: UserRegisterRequest) -> AuthResponse:
    try:
        return await auth_service.register(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
async def login(payload: UserLoginRequest) -> AuthResponse:
    try:
        return await auth_service.login(payload)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me", response_model=UserPublic)
async def me(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    return current_user


@router.patch("/me", response_model=UserPublic)
async def update_me(payload: UserUpdateRequest, current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    try:
        return await auth_service.update_profile(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    payload: PasswordChangeRequest,
    current_user: UserPublic = Depends(get_current_user),
) -> MessageResponse:
    try:
        await auth_service.change_password(current_user.id, payload)
        return MessageResponse(message="Password updated successfully")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: UserPublic = Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="Logged out successfully")
