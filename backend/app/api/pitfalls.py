from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.pitfall import Pitfall
from app.models.protocol import Protocol
from app.models.user import User
from app.schemas.pitfall import PitfallCreate, PitfallRead

router = APIRouter(prefix="/protocols/{protocol_id}/pitfalls", tags=["pitfalls"])


async def get_visible_protocol(protocol_id: int, session: AsyncSession, current_user: User) -> Protocol:
    result = await session.execute(select(Protocol).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()
    if protocol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocol not found")
    return protocol


@router.get("", response_model=list[PitfallRead])
async def list_pitfalls(
    protocol_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await get_visible_protocol(protocol_id, session, current_user)
    result = await session.execute(
        select(Pitfall)
        .options(selectinload(Pitfall.author))
        .where(Pitfall.protocol_id == protocol_id)
        .order_by(Pitfall.step_order.asc(), Pitfall.created_at.desc(), Pitfall.id.desc())
    )
    return result.scalars().all()


@router.post("", response_model=PitfallRead, status_code=status.HTTP_201_CREATED)
async def create_pitfall(
    protocol_id: int,
    payload: PitfallCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await get_visible_protocol(protocol_id, session, current_user)
    pitfall = Pitfall(
        protocol_id=protocol_id,
        step_order=payload.step_order,
        author_id=current_user.id,
        content=payload.content,
    )
    session.add(pitfall)
    await session.commit()
    result = await session.execute(select(Pitfall).options(selectinload(Pitfall.author)).where(Pitfall.id == pitfall.id))
    return result.scalar_one()
