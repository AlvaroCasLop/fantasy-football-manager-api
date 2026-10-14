from typing import Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from src.app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


class UserTokenPayload(BaseModel):
    id: str
    email: str | None = None
    role: str = "authenticated"
    user_metadata: dict[str, Any] = {}
    app_metadata: dict[str, Any] = {}


def verify_supabase_token(token: str) -> UserTokenPayload:
    """Verifies a Supabase-issued JWT and returns the parsed payload."""
    if not settings.SUPABASE_JWT_SECRET:
        # In local development without secret configured, provide a fallback warning or dev user
        if not settings.is_production:
            try:
                # Unverified decode for local testing when secret is omitted
                unverified = jwt.decode(token, options={"verify_signature": False})
                return UserTokenPayload(
                    id=unverified.get("sub", "dev-user-id"),
                    email=unverified.get("email"),
                    role=unverified.get("role", "authenticated"),
                    user_metadata=unverified.get("user_metadata", {}),
                    app_metadata=unverified.get("app_metadata", {}),
                )
            except Exception:
                return UserTokenPayload(id="dev-user-id", email="dev@fantasyfootball.local")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_JWT_SECRET is not configured on the server",
        )

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Supabase aud is typically "authenticated"
        )
        return UserTokenPayload(
            id=payload["sub"],
            email=payload.get("email"),
            role=payload.get("role", "authenticated"),
            user_metadata=payload.get("user_metadata", {}),
            app_metadata=payload.get("app_metadata", {}),
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserTokenPayload:
    """Dependency that requires a valid Supabase JWT Bearer token."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_supabase_token(credentials.credentials)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserTokenPayload | None:
    """Dependency that extracts user if token is provided, returns None otherwise."""
    if not credentials or credentials.scheme.lower() != "bearer":
        return None
    try:
        return verify_supabase_token(credentials.credentials)
    except HTTPException:
        return None
