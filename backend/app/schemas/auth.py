"""Authentication schemas for request and response serialization."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserLogin(BaseModel):
    """Payload for user login."""
    email: EmailStr
    password: str = Field(..., min_length=4)


class UserRegister(BaseModel):
    """Payload for registering a new user."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[str] = "admin"


class UserOut(BaseModel):
    """Public user profile response."""
    id: str
    name: str
    email: EmailStr
    role: str
    created_at: datetime


class Token(BaseModel):
    """JWT Token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserOut
