from datetime import datetime

from pydantic import BaseModel, Field


class ProtocolFolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    parent_id: int | None = None


class ProtocolFolderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    parent_id: int | None = None


class ProtocolFolderRead(BaseModel):
    id: int
    owner_id: int
    parent_id: int | None
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
