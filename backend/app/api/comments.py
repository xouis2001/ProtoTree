from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.comment import Comment
from app.models.protocol import Protocol
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead, CommentWithProtocolRead

router = APIRouter(prefix="/protocols/{protocol_id}/comments", tags=["comments"])
me_router = APIRouter(prefix="/me/comments", tags=["comments"])


async def get_visible_protocol(protocol_id: int, session: AsyncSession, current_user: User) -> Protocol:
    result = await session.execute(select(Protocol).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()
    if protocol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocol not found")
    return protocol


@router.get("", response_model=list[CommentRead])
async def list_comments(
    protocol_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await get_visible_protocol(protocol_id, session, current_user)
    result = await session.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.protocol_id == protocol_id)
        .order_by(Comment.step_order.asc().nullsfirst(), Comment.created_at.desc(), Comment.id.desc())
    )
    return result.scalars().all()


@router.post("", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment(
    protocol_id: int,
    payload: CommentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await get_visible_protocol(protocol_id, session, current_user)
    comment = Comment(
        protocol_id=protocol_id,
        step_order=payload.step_order,
        author_id=current_user.id,
        content=payload.content,
    )
    session.add(comment)
    await session.commit()
    result = await session.execute(select(Comment).options(selectinload(Comment.author)).where(Comment.id == comment.id))
    return result.scalar_one()


@me_router.get("/received", response_model=list[CommentWithProtocolRead])
async def list_received_comments(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Comment)
        .join(Comment.protocol)
        .options(selectinload(Comment.author), selectinload(Comment.protocol).selectinload(Protocol.author))
        .where(Protocol.author_id == current_user.id, Comment.author_id != current_user.id)
        .order_by(Comment.created_at.desc(), Comment.id.desc())
        .limit(10)
    )
    return result.scalars().all()
