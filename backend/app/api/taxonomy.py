from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.taxonomy import ProtocolCategory, ProtocolTag, ProtocolTagGroup, TaxonomySource, TaxonomyStatus
from app.models.user import User
from app.schemas.taxonomy import ProtocolTagGroupRead, ProtocolTagRead, TagCreate, TagGroupCreate, TaxonomyResponse
from app.services.taxonomy import normalize_taxonomy_name

router = APIRouter(prefix="/taxonomy", tags=["taxonomy"])


@router.get("", response_model=TaxonomyResponse)
async def get_taxonomy(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(ProtocolCategory)
        .options(selectinload(ProtocolCategory.tag_groups).selectinload(ProtocolTagGroup.tags))
        .where(ProtocolCategory.status == TaxonomyStatus.active)
        .order_by(ProtocolCategory.sort_order, ProtocolCategory.name)
    )
    categories = result.scalars().unique().all()
    for category in categories:
        category.tag_groups = sorted([group for group in category.tag_groups if group.status == TaxonomyStatus.active], key=lambda group: (group.sort_order, group.name))
        for group in category.tag_groups:
            group.tags = sorted([tag for tag in group.tags if tag.status == TaxonomyStatus.active], key=lambda tag: (0 if tag.source == TaxonomySource.official else 1, -tag.usage_count, tag.sort_order, tag.name))
    return TaxonomyResponse(categories=categories)


@router.post("/tag-groups", response_model=ProtocolTagGroupRead, status_code=status.HTTP_201_CREATED)
async def create_tag_group(
    payload: TagGroupCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="标签组名称不能为空")
    category = await session.get(ProtocolCategory, payload.category_id)
    if category is None or category.status != TaxonomyStatus.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="一级分类不存在")
    normalized_name = normalize_taxonomy_name(name)
    existing = await session.scalar(select(ProtocolTagGroup).where(ProtocolTagGroup.category_id == payload.category_id, ProtocolTagGroup.normalized_name == normalized_name, ProtocolTagGroup.status == TaxonomyStatus.active))
    if existing is not None:
        return existing
    group = ProtocolTagGroup(
        category_id=payload.category_id,
        name=name,
        normalized_name=normalized_name,
        description=payload.description.strip(),
        source=TaxonomySource.user,
        status=TaxonomyStatus.active,
        created_by_id=current_user.id,
    )
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group


@router.post("/tags", response_model=ProtocolTagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(
    payload: TagCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="标签名称不能为空")
    category = await session.get(ProtocolCategory, payload.category_id)
    if category is None or category.status != TaxonomyStatus.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="一级分类不存在")
    group = await session.get(ProtocolTagGroup, payload.tag_group_id)
    if group is None or group.status != TaxonomyStatus.active or group.category_id != payload.category_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签组不存在")
    normalized_name = normalize_taxonomy_name(name)
    existing = await session.scalar(select(ProtocolTag).where(ProtocolTag.category_id == payload.category_id, ProtocolTag.tag_group_id == payload.tag_group_id, ProtocolTag.normalized_name == normalized_name, ProtocolTag.status == TaxonomyStatus.active))
    if existing is not None:
        return existing
    tag = ProtocolTag(
        category_id=payload.category_id,
        tag_group_id=payload.tag_group_id,
        name=name,
        normalized_name=normalized_name,
        description=payload.description.strip(),
        source=TaxonomySource.user,
        status=TaxonomyStatus.active,
        created_by_id=current_user.id,
    )
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag
