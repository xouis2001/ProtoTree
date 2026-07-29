from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.db.session import get_session
from app.models.email_outbox import EmailOutbox
from app.models.user import AuditLog, User
from app.schemas.user import AdminUserUpdate, AuditLogRead, UserRead
from app.services.audit import log_action

router = APIRouter(prefix="/admin", tags=["admin"])
ALLOWED_APPROVAL_STATUSES = {"pending", "approved", "rejected"}


@router.get("/users", response_model=list[UserRead])
async def list_users(
    q: str | None = Query(default=None, description="search name/email"),
    approval_status: str | None = Query(default=None, description="pending/approved/rejected"),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    stmt = select(User).where(User.onboarding_completed.is_(True)).order_by(User.created_at.desc())
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((User.name.ilike(like)) | (User.email.ilike(like)))
    if approval_status:
        if approval_status not in ALLOWED_APPROVAL_STATUSES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid approval_status")
        stmt = stmt.where(User.approval_status == approval_status)
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
    # Serialize competing approvals. The second administrator observes the
    # committed state and therefore neither changes approver metadata nor queues
    # another message.
    result = await session.execute(select(User).where(User.id == user_id).with_for_update())
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Guard: an admin cannot demote or disable their own account (avoid lockout).
    if user.id == admin.id:
        if payload.is_admin is False or payload.is_active is False or payload.approval_status in {"pending", "rejected"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot revoke your own admin/active status")

    previous_approval_status = user.approval_status
    changes: dict = {}
    now = datetime.now(UTC)
    if payload.is_admin is not None and payload.is_admin != user.is_admin:
        # Guard: prevent removing the last remaining admin.
        if payload.is_admin is False:
            admin_count = await session.execute(select(func.count()).select_from(User).where(User.is_admin.is_(True)))
            if (admin_count.scalar() or 0) <= 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the last admin")
        user.is_admin = payload.is_admin
        changes["is_admin"] = payload.is_admin
    if payload.approval_status is not None:
        if payload.approval_status not in ALLOWED_APPROVAL_STATUSES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid approval_status")
        if payload.approval_status != user.approval_status:
            user.approval_status = payload.approval_status
            changes["approval_status"] = payload.approval_status
        if payload.approval_status == "approved" and previous_approval_status != "approved":
            if not user.is_active:
                user.is_active = True
                changes["is_active"] = True
            user.approved_at = now
            user.approved_by_id = admin.id
            changes["approved_by_id"] = admin.id
        elif payload.approval_status in {"pending", "rejected"} and user.is_active:
            user.is_active = False
            changes["is_active"] = False
    if payload.is_active is not None and payload.is_active != user.is_active:
        user.is_active = payload.is_active
        changes["is_active"] = payload.is_active
        if payload.is_active and user.approval_status != "approved":
            user.approval_status = "approved"
            user.approved_at = now
            user.approved_by_id = admin.id
            changes["approval_status"] = "approved"
            changes["approved_by_id"] = admin.id

    first_approval = previous_approval_status == "pending" and user.approval_status == "approved"
    if first_approval:
        session.add(EmailOutbox(
            event_key=f"registration_approved:{user.id}",
            recipient=user.email,
            template="registration_approved_user",
            payload={"user_id": user.id, "name": user.name, "email": user.email},
        ))

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
