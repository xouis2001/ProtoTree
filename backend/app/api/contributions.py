from collections.abc import Iterable

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.comment import Comment
from app.models.protocol import Protocol
from app.models.resource import AgentSkillResource, AnalysisToolResource, CommercialProtocolResource, ImageMacroResource
from app.models.star import ProtocolStar
from app.models.user import User
from app.schemas.contribution import ContributionProfile, ContributionProfileLeaderboardItem, ContributionProfileLeaderboards, ContributionProfileModule, ContributionSummary

router = APIRouter(tags=["contributions"])
SYSTEM_CONTRIBUTION_EMAILS = {"protocol-book@prototree.org", "protocol-book@prototree.local"}


@router.get("/me/contributions", response_model=ContributionSummary)
async def my_contributions(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    stats = await build_profile_stats(session, current_user.id)
    derived_score = (
        stats["protocol_count"] * 10
        + stats["forked_count"] * 5
        + stats["comment_count"] * 2
        + stats["star_received_count"]
        + stats["commercial_protocol_count"] * 5
        + stats["image_macro_count"] * 3
        + stats["analysis_tool_count"] * 3
        + stats["agent_skill_count"] * 3
    )
    return ContributionSummary(user_id=current_user.id, score=derived_score, events=[])


@router.get("/me/contribution-profile", response_model=ContributionProfile)
async def my_contribution_profile(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    stats = await build_profile_stats(session, current_user.id)
    return build_profile(current_user, stats)


@router.get("/contribution-profile/leaderboards", response_model=ContributionProfileLeaderboards)
async def contribution_profile_leaderboards(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    users_result = await session.execute(select(User).where(User.email.not_in(SYSTEM_CONTRIBUTION_EMAILS), User.is_active.is_(True), ~User.email.like("deactivated\\_%", escape="\\")).order_by(User.created_at.asc()))
    users = users_result.scalars().all()
    items = {user.id: {"user": user, **empty_stats()} for user in users}

    count_sets = {
        "protocol_count": await _count_protocols(session),
        "update_count": await _count_maintained_protocols(session),
        "comment_count": await _count_comments(session),
        "star_received_count": await _count_received_stars(session),
        "forked_count": await _count_forks_received(session),
        "commercial_protocol_count": await _count_resource_authors(session, CommercialProtocolResource),
        "image_macro_count": await _count_resource_authors(session, ImageMacroResource),
        "analysis_tool_count": await _count_resource_authors(session, AnalysisToolResource),
        "agent_skill_count": await _count_resource_authors(session, AgentSkillResource),
    }
    for field, rows in count_sets.items():
        for user_id, value in rows:
            if user_id in items:
                items[user_id][field] = int(value or 0)

    values = list(items.values())
    return ContributionProfileLeaderboards(
        protocol_count=sort_leaderboard(values, "protocol_count"),
        update_count=sort_leaderboard(values, "update_count"),
        comment_count=sort_leaderboard(values, "comment_count"),
        star_received_count=sort_leaderboard(values, "star_received_count"),
        forked_count=sort_leaderboard(values, "forked_count"),
        commercial_protocol_count=sort_leaderboard(values, "commercial_protocol_count"),
        image_macro_count=sort_leaderboard(values, "image_macro_count"),
        analysis_tool_count=sort_leaderboard(values, "analysis_tool_count"),
        agent_skill_count=sort_leaderboard(values, "agent_skill_count"),
    )


async def build_profile_stats(session: AsyncSession, user_id: int) -> dict[str, int]:
    stats = empty_stats()
    stats["protocol_count"] = await scalar_count(session, select(func.count(Protocol.id)).where(Protocol.author_id == user_id))
    stats["update_count"] = await scalar_count(session, select(func.count(Protocol.id)).where(Protocol.author_id == user_id, Protocol.updated_at > Protocol.created_at))
    stats["comment_count"] = await scalar_count(session, select(func.count(Comment.id)).where(Comment.author_id == user_id))
    stats["star_received_count"] = await scalar_count(session, select(func.count(ProtocolStar.id)).join(Protocol, ProtocolStar.protocol_id == Protocol.id).where(Protocol.author_id == user_id, ProtocolStar.user_id != user_id))
    stats["forked_count"] = await scalar_count(session, select(func.count(Protocol.id)).where(Protocol.parent_id.in_(select(Protocol.id).where(Protocol.author_id == user_id)), Protocol.author_id != user_id))
    stats["commercial_protocol_count"] = await scalar_count(session, select(func.count(CommercialProtocolResource.id)).where(CommercialProtocolResource.author_id == user_id))
    stats["image_macro_count"] = await scalar_count(session, select(func.count(ImageMacroResource.id)).where(ImageMacroResource.author_id == user_id))
    stats["analysis_tool_count"] = await scalar_count(session, select(func.count(AnalysisToolResource.id)).where(AnalysisToolResource.author_id == user_id))
    stats["agent_skill_count"] = await scalar_count(session, select(func.count(AgentSkillResource.id)).where(AgentSkillResource.author_id == user_id))
    return stats


def build_profile(user: User, stats: dict[str, int]) -> ContributionProfile:
    return ContributionProfile(
        user_id=user.id,
        name=user.name,
        avatar=user.avatar,
                avatar_config=user.avatar_config,
        protocol_publishing=ContributionProfileModule(label="Published protocols", value=stats["protocol_count"]),
        protocol_maintenance=ContributionProfileModule(label="Maintained protocols", value=stats["update_count"]),
        discussion=ContributionProfileModule(label="Comments", value=stats["comment_count"]),
        impact=[
            ContributionProfileModule(label="Stars received", value=stats["star_received_count"]),
            ContributionProfileModule(label="Forks received", value=stats["forked_count"]),
        ],
        special_contributions=[
            ContributionProfileModule(label="Commercial protocols", value=stats["commercial_protocol_count"]),
            ContributionProfileModule(label="ImageJ macros", value=stats["image_macro_count"]),
            ContributionProfileModule(label="Analysis tools", value=stats["analysis_tool_count"]),
            ContributionProfileModule(label="Agent skills", value=stats["agent_skill_count"]),
        ],
    )


async def scalar_count(session: AsyncSession, stmt) -> int:
    return int(await session.scalar(stmt) or 0)


async def _count_protocols(session: AsyncSession) -> list[tuple[int, int]]:
    result = await session.execute(select(Protocol.author_id, func.count(Protocol.id)).group_by(Protocol.author_id))
    return [(user_id, int(value or 0)) for user_id, value in result.all()]


async def _count_maintained_protocols(session: AsyncSession) -> list[tuple[int, int]]:
    result = await session.execute(
        select(Protocol.author_id, func.count(Protocol.id))
        .where(Protocol.updated_at > Protocol.created_at)
        .group_by(Protocol.author_id)
    )
    return [(user_id, int(value or 0)) for user_id, value in result.all()]


async def _count_comments(session: AsyncSession) -> list[tuple[int, int]]:
    result = await session.execute(select(Comment.author_id, func.count(Comment.id)).group_by(Comment.author_id))
    return [(user_id, int(value or 0)) for user_id, value in result.all()]


async def _count_received_stars(session: AsyncSession) -> list[tuple[int, int]]:
    result = await session.execute(select(Protocol.author_id, func.count(ProtocolStar.id)).join(ProtocolStar, ProtocolStar.protocol_id == Protocol.id).where(ProtocolStar.user_id != Protocol.author_id).group_by(Protocol.author_id))
    return [(user_id, int(value or 0)) for user_id, value in result.all()]


async def _count_forks_received(session: AsyncSession) -> list[tuple[int, int]]:
    parent = Protocol.__table__.alias("parent_protocols")
    result = await session.execute(
        select(parent.c.author_id, func.count(Protocol.id))
        .join(parent, Protocol.parent_id == parent.c.id)
        .where(Protocol.author_id != parent.c.author_id)
        .group_by(parent.c.author_id)
    )
    return [(user_id, int(value or 0)) for user_id, value in result.all()]


async def _count_resource_authors(session: AsyncSession, model) -> list[tuple[int, int]]:
    result = await session.execute(select(model.author_id, func.count(model.id)).where(model.author_id.is_not(None)).group_by(model.author_id))
    return [(user_id, int(value or 0)) for user_id, value in result.all()]


def empty_stats() -> dict[str, int]:
    return {
        "protocol_count": 0,
        "update_count": 0,
        "comment_count": 0,
        "star_received_count": 0,
        "forked_count": 0,
        "commercial_protocol_count": 0,
        "image_macro_count": 0,
        "analysis_tool_count": 0,
        "agent_skill_count": 0,
    }


def sort_leaderboard(items: Iterable[dict], field: str) -> list[ContributionProfileLeaderboardItem]:
    return [
        ContributionProfileLeaderboardItem(
            user_id=item["user"].id,
            name=item["user"].name,
            avatar=item["user"].avatar,
            avatar_config=item["user"].avatar_config,
            value=int(item[field] or 0),
        )
        for item in sorted(items, key=lambda item: (-int(item[field] or 0), item["user"].name, item["user"].id))[:20]
    ]
