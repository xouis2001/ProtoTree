from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuditLog


def client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


async def log_action(
    session: AsyncSession,
    action: str,
    *,
    user_id: int | None = None,
    actor_email: str | None = None,
    target: str | None = None,
    detail: dict | None = None,
    request: Request | None = None,
    commit: bool = True,
) -> None:
    """Write an audit log row. Safe to call within a request handler."""
    entry = AuditLog(
        user_id=user_id,
        actor_email=actor_email,
        action=action,
        target=target,
        detail=detail,
        ip=client_ip(request),
    )
    session.add(entry)
    if commit:
        await session.commit()
