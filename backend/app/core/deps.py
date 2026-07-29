from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, decode_token_full
from app.db.session import get_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
onboarding_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    response: Response,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    payload = decode_token_full(token)
    if payload is None or payload.get("typ") != "access" or payload.get("sub") is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials") from None
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if getattr(user, "approval_status", "approved") != "approved":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not approved")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    # Sliding renewal: if remaining lifetime is below threshold, issue a fresh token.
    exp = payload.get("exp")
    if exp is not None:
        remaining = datetime.fromtimestamp(exp, tz=UTC) - datetime.now(UTC)
        if remaining.total_seconds() < settings.sliding_renew_threshold_minutes * 60:
            fresh = create_access_token(user_id, expires_minutes=settings.access_token_expire_minutes)
            response.headers["X-Renewed-Token"] = fresh
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privilege required")
    return current_user


async def get_onboarding_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(onboarding_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired onboarding token")
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise error
    payload = decode_token_full(credentials.credentials)
    if not payload or payload.get("typ") != "onboarding" or not payload.get("sub"):
        raise error
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise error
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise error
    return user
