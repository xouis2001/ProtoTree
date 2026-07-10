from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.models.protocol import ProtocolSource, ProtocolVisibility
from app.schemas.structured import StructuredProtocol
from app.schemas.user import UserRead


class ProtocolBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    abstract: str = ""
    raw_text: str = ""
    structured: StructuredProtocol = Field(default_factory=StructuredProtocol)
    version_label: str = "v1.0"
    folder_id: int | None = None
    source: ProtocolSource = ProtocolSource.user


class ProtocolCreate(ProtocolBase):
    pass


class ProtocolUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    abstract: str | None = None
    raw_text: str | None = None
    structured: StructuredProtocol | None = None
    version_label: str | None = None
    folder_id: int | None = None
    source: ProtocolSource | None = None


class ProtocolFork(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    abstract: str | None = None
    raw_text: str | None = None
    structured: StructuredProtocol | None = None
    version_label: str = "fork"
    folder_id: int | None = None


class ProtocolRead(ProtocolBase):
    id: int
    root_id: int | None
    parent_id: int | None
    author_id: int
    author: UserRead
    created_at: datetime

    model_config = {"from_attributes": True}


class ProtocolListItem(BaseModel):
    id: int
    root_id: int | None
    parent_id: int | None
    title: str
    abstract: str
    author_id: int
    folder_id: int | None
    source: ProtocolSource
    author: UserRead
    version_label: str
    structured: StructuredProtocol
    star_count: int = 0
    starred_by_me: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ProtocolListResponse(BaseModel):
    items: list[ProtocolListItem]
    total: int
    page: int
    page_size: int
    pages: int


class ProtocolTreeNode(ProtocolListItem):
    author: UserRead
    children: list["ProtocolTreeNode"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProtocolDiffEntry(BaseModel):
    section: str
    path: str
    change_type: str
    before: Any = None
    after: Any = None


class ProtocolDiffResponse(BaseModel):
    source_id: int
    target_id: int
    source_title: str
    target_title: str
    summary: dict[str, int]
    changes: list[ProtocolDiffEntry] = Field(default_factory=list)
