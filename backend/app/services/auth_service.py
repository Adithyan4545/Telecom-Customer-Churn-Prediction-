"""Authentication and user management service layer."""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from bson import ObjectId
from fastapi import HTTPException, status

from backend.app.config import settings
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.database import get_database
from backend.app.schemas.auth import UserLogin, UserRegister, Token, UserOut

logger = logging.getLogger("telecom.auth")


class AuthService:
    """Manages credentials, user registration, and authentication tokens."""

    async def initialize_default_admin(self) -> None:
        """Seeds initial administrator account if no users exist."""
        try:
            db = get_database()
            admin_user = await db.users.find_one({"email": settings.ADMIN_EMAIL})
            if not admin_user:
                logger.info("Default administrator not found. Seeding initial admin account...")
                hashed_pw = get_password_hash(settings.ADMIN_PASSWORD)
                new_admin = {
                    "name": settings.ADMIN_NAME,
                    "email": settings.ADMIN_EMAIL,
                    "hashed_password": hashed_pw,
                    "role": "admin",
                    "created_at": datetime.now(timezone.utc),
                }
                await db.users.insert_one(new_admin)
                logger.info("Seeded administrator account: %s", settings.ADMIN_EMAIL)
            else:
                logger.info("Administrator account verified: %s", settings.ADMIN_EMAIL)
        except Exception as e:
            logger.error("Error verifying/seeding default admin: %s", e)

    async def authenticate_user(self, login_data: UserLogin) -> Token:
        """Validates credentials and returns JWT access token."""
        db = get_database()
        user = await db.users.find_one({"email": login_data.email})
        if not user or not verify_password(login_data.password, user.get("hashed_password", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token(data={"sub": user["email"], "role": user.get("role", "admin"), "name": user.get("name", "")})
        user_out = UserOut(
            id=str(user["_id"]),
            name=user.get("name", ""),
            email=user.get("email", ""),
            role=user.get("role", "admin"),
            created_at=user.get("created_at", datetime.now(timezone.utc)),
        )
        return Token(access_token=token, token_type="bearer", user=user_out)

    async def register_user(self, reg_data: UserRegister) -> UserOut:
        """Registers a new user."""
        db = get_database()
        existing = await db.users.find_one({"email": reg_data.email})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists",
            )

        hashed = get_password_hash(reg_data.password)
        now = datetime.now(timezone.utc)
        doc = {
            "name": reg_data.name.strip(),
            "email": reg_data.email.strip().lower(),
            "hashed_password": hashed,
            "role": reg_data.role or "analyst",
            "created_at": now,
        }
        res = await db.users.insert_one(doc)
        return UserOut(
            id=str(res.inserted_id),
            name=doc["name"],
            email=doc["email"],
            role=doc["role"],
            created_at=now,
        )

    async def get_user_by_email(self, email: str) -> Optional[UserOut]:
        """Looks up user profile by email address."""
        db = get_database()
        user = await db.users.find_one({"email": email})
        if not user:
            return None
        return UserOut(
            id=str(user["_id"]),
            name=user.get("name", ""),
            email=user.get("email", ""),
            role=user.get("role", "admin"),
            created_at=user.get("created_at", datetime.now(timezone.utc)),
        )


auth_service = AuthService()
