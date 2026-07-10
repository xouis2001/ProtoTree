from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserRead


class PitfallCreate(BaseModel):
    step_order: int = Field(ge=0)
    content: str = Field(min_length=1, max_length=2000)


class PitfallRead(BaseModel):
    id: int
    protocol_id: int
    step_order: int
    author_id: int
    author: UserRead
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
