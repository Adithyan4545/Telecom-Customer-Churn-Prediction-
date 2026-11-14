"""Authentication router endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.core.security import get_current_user
from backend.app.schemas.auth import UserLogin, UserRegister, Token, UserOut
from backend.app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Authenticates user and returns JWT token."""
    return await auth_service.authenticate_user(login_data)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(reg_data: UserRegister):
    """Registers a new administrative user."""
    return await auth_service.register_user(reg_data)


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Retrieves profile of currently authenticated user."""
    user = await auth_service.get_user_by_email(current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
