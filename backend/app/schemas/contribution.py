from datetime import datetime

from pydantic import BaseModel

from app.models.contribution import ContributionEventType


class ContributionEventRead(BaseModel):
    id: int
    user_id: int
    event_type: ContributionEventType
    score_delta: int
    protocol_id: int | None
    related_protocol_id: int | None
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ContributionSummary(BaseModel):
    user_id: int
    score: int
    events: list[ContributionEventRead]


class ContributionProfileModule(BaseModel):
    label: str
    value: int


class ContributionProfile(BaseModel):
    user_id: int
    name: str
    avatar: str
    protocol_publishing: ContributionProfileModule
    protocol_maintenance: ContributionProfileModule
    discussion: ContributionProfileModule
    impact: list[ContributionProfileModule]
    special_contributions: list[ContributionProfileModule]


class ContributionProfileLeaderboardItem(BaseModel):
    user_id: int
    name: str
    avatar: str
    avatar_config: dict | None = None
    value: int


class ContributionProfileLeaderboards(BaseModel):
    protocol_count: list[ContributionProfileLeaderboardItem]
    update_count: list[ContributionProfileLeaderboardItem]
    comment_count: list[ContributionProfileLeaderboardItem]
    star_received_count: list[ContributionProfileLeaderboardItem]
    forked_count: list[ContributionProfileLeaderboardItem]
    commercial_protocol_count: list[ContributionProfileLeaderboardItem]
    image_macro_count: list[ContributionProfileLeaderboardItem]
    analysis_tool_count: list[ContributionProfileLeaderboardItem]
    agent_skill_count: list[ContributionProfileLeaderboardItem]
