from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    avatar_config: dict | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    avatar: str
    avatar_config: dict | None = None
    is_admin: bool
    is_active: bool = True
    contribution_score: int
    projects: list[str] = Field(default_factory=list)
    last_login: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class UserPasswordUpdate(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class UserDeactivate(BaseModel):
    current_password: str = Field(min_length=1)


class UserProjectsUpdate(BaseModel):
    projects: list[str] = Field(default_factory=list)


class AvatarConfigUpdate(BaseModel):
    avatar_config: dict


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=8, max_length=128)
    password: str = Field(min_length=8, max_length=128)


class AdminUserUpdate(BaseModel):
    is_admin: bool | None = None
    is_active: bool | None = None


class AuditLogRead(BaseModel):
    id: int
    user_id: int | None = None
    actor_email: str | None = None
    action: str
    target: str | None = None
    detail: dict | None = None
    ip: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
