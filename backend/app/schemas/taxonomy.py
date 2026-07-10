from datetime import datetime

from pydantic import BaseModel, Field

from app.models.taxonomy import TaxonomySource, TaxonomyStatus


class ProtocolTagRead(BaseModel):
    id: int
    category_id: int
    tag_group_id: int
    name: str
    description: str
    source: TaxonomySource
    status: TaxonomyStatus
    usage_count: int
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProtocolTagGroupRead(BaseModel):
    id: int
    category_id: int
    name: str
    description: str
    source: TaxonomySource
    status: TaxonomyStatus
    usage_count: int
    sort_order: int
    created_at: datetime
    tags: list[ProtocolTagRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProtocolCategoryRead(BaseModel):
    id: int
    name: str
    description: str
    color: str
    source: TaxonomySource
    status: TaxonomyStatus
    usage_count: int
    sort_order: int
    created_at: datetime
    tag_groups: list[ProtocolTagGroupRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TaxonomyResponse(BaseModel):
    categories: list[ProtocolCategoryRead]


class TagGroupCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=120)
    description: str = ""


class TagCreate(BaseModel):
    category_id: int
    tag_group_id: int
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
