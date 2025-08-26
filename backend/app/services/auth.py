"""Authentication service for handling JWT tokens and password validation."""

from datetime import UTC, datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings


class TokenData(BaseModel):
    """JWT token data."""

    username: str
    user_id: str
    role: str
    exp: datetime


class AuthService:
    """Service for authentication operations."""

    # Password hashing context
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # JWT settings
    SECRET_KEY = (
        settings.SECRET_KEY
        if hasattr(settings, "SECRET_KEY")
        else "your-secret-key-change-in-production"
    )
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        result: bool = cls.pwd_context.verify(plain_password, hashed_password)
        return result

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash a password."""
        result: str = cls.pwd_context.hash(password)
        return result

    @classmethod
    def create_access_token(
        cls,
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        encoded_jwt: str = jwt.encode(
            to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM
        )
        return encoded_jwt

    @classmethod
    def decode_access_token(cls, token: str) -> Optional[TokenData]:
        """Decode and validate a JWT access token."""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            role: str = payload.get("role")
            exp: float = payload.get("exp")

            if username is None or user_id is None:
                return None

            return TokenData(
                username=username,
                user_id=user_id,
                role=role,
                exp=datetime.fromtimestamp(exp, UTC),
            )
        except JWTError:
            return None
