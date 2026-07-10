from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.protocol import ProtocolListItem
from app.schemas.user import UserRead


class CommentCreate(BaseModel):
    step_order: int | None = Field(default=None, ge=1)
    content: str = Field(min_length=1, max_length=2000)


class CommentRead(BaseModel):
    id: int
    protocol_id: int
    step_order: int | None
    author_id: int
    author: UserRead
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentWithProtocolRead(CommentRead):
    protocol: ProtocolListItem
