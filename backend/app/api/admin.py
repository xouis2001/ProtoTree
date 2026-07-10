from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.db.session import get_session
from app.models.user import AuditLog, User
from app.schemas.user import AdminUserUpdate, AuditLogRead, UserRead
from app.services.audit import log_action

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead])
async def list_users(
    q: str | None = Query(default=None, description="search name/email"),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    stmt = select(User).order_by(User.created_at.desc())
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((User.name.ilike(like)) | (User.email.ilike(like)))
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Guard: an admin cannot demote or disable their own account (avoid lockout).
    if user.id == admin.id:
        if payload.is_admin is False or payload.is_active is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot revoke your own admin/active status")

    changes: dict = {}
    if payload.is_admin is not None and payload.is_admin != user.is_admin:
        # Guard: prevent removing the last remaining admin.
        if payload.is_admin is False:
            admin_count = await session.execute(select(func.count()).select_from(User).where(User.is_admin.is_(True)))
            if (admin_count.scalar() or 0) <= 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the last admin")
        user.is_admin = payload.is_admin
        changes["is_admin"] = payload.is_admin
    if payload.is_active is not None and payload.is_active != user.is_active:
        user.is_active = payload.is_active
        changes["is_active"] = payload.is_active

    if changes:
        session.add(user)
        await log_action(
            session, "admin.update_user", user_id=admin.id, actor_email=admin.email,
            target=user.email, detail=changes, request=request, commit=False,
        )
        await session.commit()
        await session.refresh(user)
    return user


@router.get("/audit-logs", response_model=list[AuditLogRead])
async def list_audit_logs(
    action: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        stmt = stmt.where(AuditLog.action == action)
    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())
