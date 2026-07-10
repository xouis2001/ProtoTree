import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import (
    AvatarConfigUpdate,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    UserProjectsUpdate,
    UserProfileUpdate,
    UserPasswordUpdate,
    UserDeactivate,
    UserRead,
)
from app.services.audit import log_action
from app.services.mailer import send_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, request: Request, session: AsyncSession = Depends(get_session)):
    existing = await session.execute(select(User).where(User.email == payload.email.lower()))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # First-ever user becomes admin bootstrap; open registration otherwise.
    first = await session.execute(select(User.id).limit(1))
    is_first = first.scalar_one_or_none() is None

    user = User(
        name=payload.name,
        email=payload.email.lower(),
        password_hash=get_password_hash(payload.password),
        avatar="",
        avatar_config=payload.avatar_config,
        is_admin=is_first,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    await log_action(session, "user.register", user_id=user.id, actor_email=user.email, request=request)

    access_token = create_access_token(str(user.id))
    return Token(access_token=access_token, user=UserRead.model_validate(user))


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, request: Request, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    user.last_login = datetime.now(UTC)
    session.add(user)

    expire_minutes = settings.remember_token_expire_minutes if payload.remember else settings.access_token_expire_minutes
    access_token = create_access_token(str(user.id), expires_minutes=expire_minutes)

    await log_action(session, "user.login", user_id=user.id, actor_email=user.email,
                     detail={"remember": payload.remember}, request=request)

    return Token(access_token=access_token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me/profile", response_model=UserRead)
async def update_my_profile(payload: UserProfileUpdate, request: Request, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Name cannot be empty")
    current_user.name = name[:80]
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    await log_action(session, "user.update_profile", user_id=current_user.id, actor_email=current_user.email, request=request)
    return current_user


@router.put("/me/password", response_model=UserRead)
async def update_my_password(payload: UserPasswordUpdate, request: Request, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码不正确")
    current_user.password_hash = get_password_hash(payload.new_password)
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    await log_action(session, "user.update_password", user_id=current_user.id, actor_email=current_user.email, request=request)
    return current_user


@router.put("/me/projects", response_model=UserRead)
async def update_my_projects(payload: UserProjectsUpdate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    projects = []
    seen = set()
    for project in payload.projects:
        value = project.strip()
        if value and value not in seen:
            projects.append(value[:120])
            seen.add(value)
    current_user.projects = projects
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user


@router.put("/me/avatar", response_model=UserRead)
async def update_my_avatar(payload: AvatarConfigUpdate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    current_user.avatar_config = payload.avatar_config
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user


@router.post("/me/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_my_account(payload: UserDeactivate, request: Request, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码不正确")
    current_user.is_active = False
    session.add(current_user)
    await session.commit()
    await log_action(session, "user.deactivate", user_id=current_user.id, actor_email=current_user.email, request=request)
    return None

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(payload: ForgotPasswordRequest, request: Request, session: AsyncSession = Depends(get_session)):
    email = payload.email.lower().strip()
    # Emergency guard: never send SMTP to automated reset smoke-test addresses.
    # QQ SMTP was rejecting repeated test emails; keep the public 202 response.
    if email.startswith("smoketest_reset") or email.startswith("smoketest-reset") or email.startswith("reset_smoke"):
        return {"message": "If the email exists, a reset link has been sent."}
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    # Always return 202 to avoid email enumeration.
    if user is not None and user.is_active:
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.now(UTC) + timedelta(minutes=30)
        session.add(user)
        await log_action(session, "user.forgot_password", user_id=user.id, actor_email=user.email, request=request)
        await session.commit()
        reset_url = f"{settings.reset_link_base}?token={token}"
        try:
            send_reset_email(user.email, reset_url)
        except Exception:
            # Do not leak SMTP failure to client; token still stored for retry.
            pass
    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(payload: ResetPasswordRequest, request: Request, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.reset_token == payload.token))
    user = result.scalar_one_or_none()
    if user is None or user.reset_token_expires is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    expires = user.reset_token_expires
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user.password_hash = get_password_hash(payload.password)
    user.reset_token = None
    user.reset_token_expires = None
    session.add(user)
    await log_action(session, "user.reset_password", user_id=user.id, actor_email=user.email, request=request)
    await session.commit()
    return {"message": "Password has been reset."}
