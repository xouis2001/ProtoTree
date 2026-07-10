from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.comment import Comment
from app.models.contribution import ContributionEvent
from app.models.folder import ProtocolFolder
from app.models.pitfall import Pitfall
from app.models.protocol import Protocol, ProtocolSource, ProtocolVisibility
from app.models.star import ProtocolStar
from app.models.user import User
from app.schemas.protocol import (
    ProtocolCreate,
    ProtocolDiffResponse,
    ProtocolFork,
    ProtocolListResponse,
    ProtocolRead,
    ProtocolTreeNode,
    ProtocolUpdate,
)
from app.schemas.star import ProtocolStarSummary
from app.schemas.structured import ProtocolAssistFormatRequest, ProtocolParseRequest, ProtocolParseResponse
from app.services.ai_parser import assist_format_uploaded_protocol, parse_protocol_text
from app.services.document_extractor import build_plain_protocol_structured, extract_document_text
from app.services.protocol_diff import diff_protocols
from app.services.protocol_structured import normalize_structured_protocol

router = APIRouter(prefix="/protocols", tags=["protocols"])


def can_view_protocol(protocol: Protocol, current_user: User) -> bool:
    return True


def can_write_protocol(protocol: Protocol, current_user: User) -> bool:
    return protocol.author_id == current_user.id or current_user.is_admin


def is_postgres(session: AsyncSession) -> bool:
    bind = session.get_bind()
    return bind.dialect.name == "postgresql"


def taxonomy_jsonb_filters(tag_group_values: list[str], tag_values: list[str]) -> list:
    filters = []
    if tag_group_values:
        filters.append(or_(*[Protocol.structured["tag_groups"].contains([value]) for value in tag_group_values]))
    if tag_values:
        filters.append(or_(*[Protocol.structured["tags"].contains([value]) for value in tag_values]))
    return filters


def matches_taxonomy(protocol: Protocol, tag_group_values: list[str], tag_values: list[str]) -> bool:
    structured = protocol.structured or {}
    protocol_tag_groups = structured.get("tag_groups") if isinstance(structured.get("tag_groups"), list) else []
    protocol_tags = structured.get("tags") if isinstance(structured.get("tags"), list) else []
    if tag_group_values and not any(value in protocol_tag_groups for value in tag_group_values):
        return False
    if tag_values and not any(value in protocol_tags for value in tag_values):
        return False
    return True


async def validate_folder_owner(folder_id: int | None, session: AsyncSession, current_user: User) -> None:
    if folder_id is None:
        return
    result = await session.execute(select(ProtocolFolder).where(ProtocolFolder.id == folder_id, ProtocolFolder.owner_id == current_user.id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")


async def get_star_meta(protocol_ids: list[int], session: AsyncSession, current_user: User) -> dict[int, tuple[int, bool]]:
    if not protocol_ids:
        return {}
    count_result = await session.execute(
        select(ProtocolStar.protocol_id, func.count(ProtocolStar.id)).where(ProtocolStar.protocol_id.in_(protocol_ids)).group_by(ProtocolStar.protocol_id)
    )
    counts = {protocol_id: int(count) for protocol_id, count in count_result.all()}
    mine_result = await session.execute(select(ProtocolStar.protocol_id).where(ProtocolStar.protocol_id.in_(protocol_ids), ProtocolStar.user_id == current_user.id))
    mine = set(mine_result.scalars().all())
    return {protocol_id: (counts.get(protocol_id, 0), protocol_id in mine) for protocol_id in protocol_ids}


def attach_star_meta(protocol: Protocol, meta: dict[int, tuple[int, bool]]) -> Protocol:
    star_count, starred_by_me = meta.get(protocol.id, (0, False))
    setattr(protocol, "star_count", star_count)
    setattr(protocol, "starred_by_me", starred_by_me)
    return protocol


def build_tree(nodes: list[Protocol]) -> ProtocolTreeNode:
    node_map = {
        node.id: ProtocolTreeNode(
            id=node.id,
            root_id=node.root_id,
            parent_id=node.parent_id,
            title=node.title,
            abstract=node.abstract,
            author_id=node.author_id,
            folder_id=node.folder_id,
            source=getattr(node, "source", ProtocolSource.user),
            author=node.author,
            version_label=node.version_label,
            structured=node.structured,
            star_count=getattr(node, "star_count", 0),
            starred_by_me=getattr(node, "starred_by_me", False),
            created_at=node.created_at,
            children=[],
        )
        for node in nodes
    }
    root = node_map[nodes[0].root_id or nodes[0].id]
    for node in nodes:
        if node.parent_id and node.parent_id in node_map:
            node_map[node.parent_id].children.append(node_map[node.id])
    return root


@router.post("/parse", response_model=ProtocolParseResponse)
async def parse_protocol(payload: ProtocolParseRequest, current_user: User = Depends(get_current_user)):
    return await parse_protocol_text(payload.raw_text)


@router.post("/format-upload", response_model=ProtocolParseResponse)
async def format_uploaded_protocol(payload: ProtocolAssistFormatRequest, current_user: User = Depends(get_current_user)):
    return await assist_format_uploaded_protocol(payload.raw_text, payload.title_hint)


@router.post("/extract-file", response_model=ProtocolParseResponse)
@router.post("/extract-file/upload", response_model=ProtocolParseResponse)
async def extract_protocol_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    filename = file.filename or "protocol"
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF and DOCX files are supported")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    try:
        text = extract_document_text(filename, content)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to extract text from uploaded file") from exc
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No extractable text found in uploaded file")
    title = Path(filename).stem.strip() or "Uploaded Protocol"
    abstract = f"{text[:240]}..." if len(text) > 240 else text[:240]
    return ProtocolParseResponse(title=title, abstract=abstract, structured=build_plain_protocol_structured(title, text), parser="file-extract", warnings=[])


@router.post("", response_model=ProtocolRead, status_code=status.HTTP_201_CREATED)
async def create_protocol(
    payload: ProtocolCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await validate_folder_owner(payload.folder_id, session, current_user)
    protocol = Protocol(
        title=payload.title,
        abstract=payload.abstract,
        visibility=ProtocolVisibility.public,
        raw_text=payload.raw_text,
        structured=normalize_structured_protocol(payload.structured),
        version_label=payload.version_label,
        folder_id=payload.folder_id,
        source=payload.source if current_user.is_admin else ProtocolSource.user,
        author_id=current_user.id,
    )
    session.add(protocol)
    await session.flush()
    protocol.root_id = protocol.id
    await session.commit()
    result = await session.execute(select(Protocol).options(selectinload(Protocol.author)).where(Protocol.id == protocol.id))
    created = result.scalar_one()
    return attach_star_meta(created, await get_star_meta([created.id], session, current_user))


@router.get("/authors", response_model=list[dict])
async def list_protocol_authors(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(User.id, User.name, User.avatar, User.avatar_config)
        .join(Protocol, Protocol.author_id == User.id)
        .group_by(User.id)
        .order_by(User.name)
    )
    return [{"id": author_id, "name": name, "avatar": avatar, "avatar_config": avatar_config} for author_id, name, avatar, avatar_config in result.all()]


@router.get("", response_model=ProtocolListResponse)
async def list_protocols(
    q: str | None = Query(default=None),
    author_id: int | None = Query(default=None),
    source: ProtocolSource | None = Query(default=None),
    experiment_type: str | None = Query(default=None),
    experiment_subtype: str | None = Query(default=None),
    experiment_category: str | None = Query(default=None),
    tag_groups: str | None = Query(default=None),
    tags: str | None = Query(default=None),
    sort: str = Query(default="newest"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    filters = []
    stmt = select(Protocol).options(selectinload(Protocol.author))
    count_stmt = select(func.count(Protocol.id))
    if q:
        keyword = f"%{q}%"
        filters.append(or_(Protocol.title.ilike(keyword), Protocol.abstract.ilike(keyword), Protocol.raw_text.ilike(keyword), Protocol.version_label.ilike(keyword)))
    if author_id:
        filters.append(Protocol.author_id == author_id)
    if source:
        filters.append(Protocol.source == source)
    if experiment_category:
        filters.append(or_(Protocol.structured["experiment_category"].as_string() == experiment_category, Protocol.structured["experiment_type"].as_string() == experiment_category))
    elif experiment_type:
        filters.append(Protocol.structured["experiment_type"].as_string() == experiment_type)
    if experiment_subtype:
        filters.append(Protocol.structured["experiment_subtype"].as_string() == experiment_subtype)

    tag_group_values = [item.strip() for item in (tag_groups or "").split(",") if item.strip()]
    tag_values = [item.strip() for item in (tags or "").split(",") if item.strip()]
    if is_postgres(session):
        filters.extend(taxonomy_jsonb_filters(tag_group_values, tag_values))

    for condition in filters:
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    sort_options = {
        "newest": Protocol.created_at.desc(),
        "oldest": Protocol.created_at.asc(),
        "title": Protocol.title.asc(),
        "version": Protocol.version_label.asc(),
    }

    if (tag_group_values or tag_values) and not is_postgres(session):
        result = await session.execute(stmt.order_by(sort_options.get(sort, Protocol.created_at.desc())))
        filtered_protocols = [protocol for protocol in result.scalars().all() if matches_taxonomy(protocol, tag_group_values, tag_values)]
        total = len(filtered_protocols)
        protocols = filtered_protocols[(page - 1) * page_size : page * page_size]
    else:
        total = int(await session.scalar(count_stmt) or 0)
        result = await session.execute(stmt.order_by(sort_options.get(sort, Protocol.created_at.desc())).offset((page - 1) * page_size).limit(page_size))
        protocols = result.scalars().all()

    meta = await get_star_meta([protocol.id for protocol in protocols], session, current_user)
    return ProtocolListResponse(
        items=[attach_star_meta(protocol, meta) for protocol in protocols],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/starred", response_model=ProtocolListResponse)
async def list_starred_protocols(
    q: str | None = Query(default=None),
    sort: str = Query(default="newest"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    filters = [ProtocolStar.user_id == current_user.id]
    stmt = select(Protocol).join(ProtocolStar, ProtocolStar.protocol_id == Protocol.id).options(selectinload(Protocol.author))
    count_stmt = select(func.count(Protocol.id)).join(ProtocolStar, ProtocolStar.protocol_id == Protocol.id)
    if q:
        keyword = f"%{q}%"
        filters.append(or_(Protocol.title.ilike(keyword), Protocol.abstract.ilike(keyword), Protocol.raw_text.ilike(keyword), Protocol.version_label.ilike(keyword)))
    for condition in filters:
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)
    sort_options = {
        "newest": ProtocolStar.created_at.desc(),
        "oldest": ProtocolStar.created_at.asc(),
        "title": Protocol.title.asc(),
        "version": Protocol.version_label.asc(),
    }
    total = int(await session.scalar(count_stmt) or 0)
    result = await session.execute(stmt.order_by(sort_options.get(sort, ProtocolStar.created_at.desc())).offset((page - 1) * page_size).limit(page_size))
    protocols = result.scalars().all()
    meta = await get_star_meta([protocol.id for protocol in protocols], session, current_user)
    return ProtocolListResponse(
        items=[attach_star_meta(protocol, meta) for protocol in protocols],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/{protocol_id}/fork", response_model=ProtocolRead, status_code=status.HTTP_201_CREATED)
async def fork_protocol(
    protocol_id: int,
    payload: ProtocolFork,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Protocol).options(selectinload(Protocol.author)).where(Protocol.id == protocol_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocol not found")
    await validate_folder_owner(payload.folder_id, session, current_user)

    fork = Protocol(
        root_id=source.root_id or source.id,
        parent_id=source.id,
        title=payload.title if payload.title is not None else source.title,
        abstract=payload.abstract if payload.abstract is not None else source.abstract,
        visibility=ProtocolVisibility.public,
        raw_text=payload.raw_text if payload.raw_text is not None else source.raw_text,
        structured=normalize_structured_protocol(payload.structured if payload.structured is not None else source.structured),
        version_label=payload.version_label,
        folder_id=payload.folder_id,
        source=ProtocolSource.user,
        author_id=current_user.id,
    )
    session.add(fork)
    await session.commit()
    result = await session.execute(select(Protocol).options(selectinload(Protocol.author)).where(Protocol.id == fork.id))
    forked = result.scalar_one()
    return attach_star_meta(forked, await get_star_meta([forked.id], session, current_user))


@router.get("/{protocol_id}/tree", response_model=ProtocolTreeNode)
async def get_protocol_tree(
    protocol_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Protocol).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()
    if protocol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocol not found")
    root_id = protocol.root_id or protocol.id
    result = await session.execute(
        select(Protocol)
        .options(selectinload(Protocol.author))
        .where(Protocol.root_id == root_id)
        .order_by(Protocol.created_at.asc())
    )
    nodes = [node for node in result.scalars().all() if can_view_protocol(node, current_user)]
    if not nodes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocol tree not found")
    meta = await get_star_meta([node.id for node in nodes], session, current_user)
    for node in nodes:
        attach_star_meta(node, meta)
    return build_tree(nodes)


@router.get("/{protocol_id}/diff/{target_id}", response_model=ProtocolDiffResponse)
async def get_protocol_diff(
    protocol_id: int,
    target_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Protocol).where(Protocol.id.in_([protocol_id, target_id])))
    protocols = {protocol.id: protocol for protocol in result.scalars().all()}
    source = protocols.get(protocol_id)
    target = protocols.get(target_id)
    if source is None or target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocol not found")
    if (source.root_id or source.id) != (target.root_id or target.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only protocols in the same version tree can be compared")
    return diff_protocols(source, target)


@router.post("/{protocol_id}/star", response_model=ProtocolStarSummary)
async def star_protocol(
    protocol_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Protocol).options(selectinload(Protocol.author)).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()
    if protocol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocol not found")
    star_result = await session.execute(select(ProtocolStar).where(ProtocolStar.protocol_id == protocol_id, ProtocolStar.user_id == current_user.id))
    if star_result.scalar_one_or_none() is None:
        session.add(ProtocolStar(protocol_id=protocol_id, user_id=current_user.id))
        await session.commit()
    meta = await get_star_meta([protocol_id], session, current_user)
    star_count, starred_by_me = meta.get(protocol_id, (0, False))
    return ProtocolStarSummary(protocol_id=protocol_id, star_count=star_count, starred_by_me=starred_by_me)


@router.delete("/{protocol_id}/star", response_model=ProtocolStarSummary)
async def unstar_protocol(
    protocol_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Protocol).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()
    if protocol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocol not found")
    star_result = await session.execute(select(ProtocolStar).where(ProtocolStar.protocol_id == protocol_id, ProtocolStar.user_id == current_user.id))
    star = star_result.scalar_one_or_none()
    if star is not None:
        await session.delete(star)
        await session.commit()
    meta = await get_star_meta([protocol_id], session, current_user)
    star_count, starred_by_me = meta.get(protocol_id, (0, False))
    return ProtocolStarSummary(protocol_id=protocol_id, star_count=star_count, starred_by_me=starred_by_me)


@router.get("/{protocol_id}", response_model=ProtocolRead)
async def get_protocol(
    protocol_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Protocol).options(selectinload(Protocol.author)).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()
    if protocol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocol not found")
    return attach_star_meta(protocol, await get_star_meta([protocol.id], session, current_user))


@router.delete("/{protocol_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_protocol(
    protocol_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Protocol).options(selectinload(Protocol.author)).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()
    if protocol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocol not found")
    if not can_write_protocol(protocol, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author or an admin can delete this protocol")

    children_result = await session.execute(select(Protocol).where(or_(Protocol.parent_id == protocol_id, Protocol.root_id == protocol_id)))
    for child in children_result.scalars().all():
        if child.parent_id == protocol_id:
            child.parent_id = None
        if child.root_id == protocol_id:
            child.root_id = child.id
        session.add(child)

    await session.execute(delete(ContributionEvent).where(or_(ContributionEvent.protocol_id == protocol_id, ContributionEvent.related_protocol_id == protocol_id)))
    await session.execute(delete(Comment).where(Comment.protocol_id == protocol_id))
    await session.execute(delete(Pitfall).where(Pitfall.protocol_id == protocol_id))
    await session.execute(delete(ProtocolStar).where(ProtocolStar.protocol_id == protocol_id))
    await session.delete(protocol)
    await session.commit()
    return None


@router.put("/{protocol_id}", response_model=ProtocolRead)
async def update_protocol(
    protocol_id: int,
    payload: ProtocolUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Protocol).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()
    if protocol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocol not found")
    if not can_write_protocol(protocol, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author or an admin can update this protocol")

    updates = payload.model_dump(exclude_unset=True)
    if "source" in updates and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can change protocol source")
    if "folder_id" in updates and protocol.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can move this protocol")
    if "folder_id" in updates:
        await validate_folder_owner(updates["folder_id"], session, current_user)
    for key, value in updates.items():
        if key == "structured":
            value = normalize_structured_protocol(value)
        setattr(protocol, key, value)

    await session.commit()
    result = await session.execute(select(Protocol).options(selectinload(Protocol.author)).where(Protocol.id == protocol.id))
    updated = result.scalar_one()
    return attach_star_meta(updated, await get_star_meta([updated.id], session, current_user))
