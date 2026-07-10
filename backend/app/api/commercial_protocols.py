import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.resource import CommercialProtocolResource
from app.models.star import CommercialProtocolStar
from app.models.user import User
from app.schemas.commercial_protocol import CommercialProtocolRead
from app.schemas.star import ProtocolStarSummary

router = APIRouter(prefix="/commercial-protocols", tags=["commercial-protocols"])


def storage_path() -> Path:
    path = Path(settings.storage_dir) / "commercial_protocols"
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(filename: str) -> str:
    stem = Path(filename).stem or "protocol"
    cleaned = re.sub(r"[^\w\-.\u4e00-\u9fff]+", "_", stem, flags=re.UNICODE).strip("._")
    return f"{cleaned or 'protocol'}.pdf"


def to_read(item: CommercialProtocolResource, meta: dict[str, tuple[int, bool]] | None = None) -> CommercialProtocolRead:
    protocol_id = item.id
    star_count, starred_by_me = (meta or {}).get(protocol_id, (0, False))
    return CommercialProtocolRead(
        id=protocol_id,
        title=item.title,
        manufacturer=item.manufacturer,
        catalog_no=item.catalog_no,
        description=item.description,
        filename=item.original_filename,
        file_size=item.file_size,
        author_id=item.author_id,
        author_name=item.author_name,
        preview_url=f"/commercial-protocols/{protocol_id}/preview",
        download_url=f"/commercial-protocols/{protocol_id}/download",
        star_count=star_count,
        starred_by_me=starred_by_me,
        created_at=item.created_at,
    )


async def find_item(protocol_id: str, session: AsyncSession) -> CommercialProtocolResource:
    item = await session.get(CommercialProtocolResource, protocol_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commercial protocol not found")
    return item


async def get_star_meta(protocol_ids: list[str], session: AsyncSession, current_user: User) -> dict[str, tuple[int, bool]]:
    if not protocol_ids:
        return {}
    count_result = await session.execute(
        select(CommercialProtocolStar.commercial_protocol_id, func.count(CommercialProtocolStar.id))
        .where(CommercialProtocolStar.commercial_protocol_id.in_(protocol_ids))
        .group_by(CommercialProtocolStar.commercial_protocol_id)
    )
    counts = {protocol_id: int(count) for protocol_id, count in count_result.all()}
    mine_result = await session.execute(
        select(CommercialProtocolStar.commercial_protocol_id)
        .where(CommercialProtocolStar.commercial_protocol_id.in_(protocol_ids), CommercialProtocolStar.user_id == current_user.id)
    )
    mine = set(mine_result.scalars().all())
    return {protocol_id: (counts.get(protocol_id, 0), protocol_id in mine) for protocol_id in protocol_ids}


@router.get("", response_model=list[CommercialProtocolRead])
async def list_commercial_protocols(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(CommercialProtocolResource).order_by(CommercialProtocolResource.created_at.desc()))
    items = result.scalars().all()
    meta = await get_star_meta([item.id for item in items], session, current_user)
    return [to_read(item, meta) for item in items]


@router.get("/starred", response_model=list[CommercialProtocolRead])
async def list_starred_commercial_protocols(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(CommercialProtocolResource)
        .join(CommercialProtocolStar, CommercialProtocolStar.commercial_protocol_id == CommercialProtocolResource.id)
        .where(CommercialProtocolStar.user_id == current_user.id)
        .order_by(CommercialProtocolStar.created_at.desc())
    )
    items = result.scalars().all()
    meta = await get_star_meta([item.id for item in items], session, current_user)
    return [to_read(item, meta) for item in items]


@router.post("", response_model=CommercialProtocolRead, status_code=status.HTTP_201_CREATED)
@router.post("/upload", response_model=CommercialProtocolRead, status_code=status.HTTP_201_CREATED)
async def upload_commercial_protocol(
    title: str = Form(...),
    manufacturer: str = Form(...),
    catalog_no: str = Form(""),
    description: str = Form(""),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required")
    if not manufacturer.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Manufacturer is required")
    if Path(file.filename or "").suffix.lower() != ".pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported")
    protocol_id = uuid4().hex
    filename = f"{protocol_id}_{safe_filename(file.filename or 'protocol.pdf')}"
    path = storage_path() / filename
    size = 0
    with path.open("wb") as output:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            output.write(chunk)
    if size == 0:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    item = CommercialProtocolResource(
        id=protocol_id,
        title=title.strip() or Path(file.filename or "protocol").stem,
        manufacturer=manufacturer.strip(),
        catalog_no=catalog_no.strip(),
        description=description.strip(),
        filename=filename,
        original_filename=file.filename or filename,
        file_size=size,
        author_id=current_user.id,
        author_name=current_user.name,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return to_read(item, await get_star_meta([item.id], session, current_user))


@router.post("/{protocol_id}/star", response_model=ProtocolStarSummary)
async def star_commercial_protocol(
    protocol_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await find_item(protocol_id, session)
    star_result = await session.execute(
        select(CommercialProtocolStar)
        .where(CommercialProtocolStar.commercial_protocol_id == protocol_id, CommercialProtocolStar.user_id == current_user.id)
    )
    if star_result.scalar_one_or_none() is None:
        session.add(CommercialProtocolStar(commercial_protocol_id=protocol_id, user_id=current_user.id))
        await session.commit()
    meta = await get_star_meta([protocol_id], session, current_user)
    star_count, starred_by_me = meta.get(protocol_id, (0, False))
    return ProtocolStarSummary(protocol_id=0, star_count=star_count, starred_by_me=starred_by_me)


@router.delete("/{protocol_id}/star", response_model=ProtocolStarSummary)
async def unstar_commercial_protocol(
    protocol_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await find_item(protocol_id, session)
    await session.execute(
        delete(CommercialProtocolStar)
        .where(CommercialProtocolStar.commercial_protocol_id == protocol_id, CommercialProtocolStar.user_id == current_user.id)
    )
    await session.commit()
    meta = await get_star_meta([protocol_id], session, current_user)
    star_count, starred_by_me = meta.get(protocol_id, (0, False))
    return ProtocolStarSummary(protocol_id=0, star_count=star_count, starred_by_me=starred_by_me)


@router.get("/{protocol_id}/preview")
async def preview_commercial_protocol(
    protocol_id: str,
    session: AsyncSession = Depends(get_session),
):
    item = await find_item(protocol_id, session)
    path = storage_path() / item.filename
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF file not found")
    return FileResponse(path, media_type="application/pdf", filename=item.original_filename, content_disposition_type="inline")


@router.get("/{protocol_id}/download")
async def download_commercial_protocol(
    protocol_id: str,
    session: AsyncSession = Depends(get_session),
):
    item = await find_item(protocol_id, session)
    path = storage_path() / item.filename
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF file not found")
    return FileResponse(path, media_type="application/pdf", filename=item.original_filename)


@router.delete("/{protocol_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_commercial_protocol(
    protocol_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = await find_item(protocol_id, session)
    if not (current_user.is_admin or item.author_id == current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the uploader or an admin can delete this commercial protocol")
    path = storage_path() / item.filename
    path.unlink(missing_ok=True)
    await session.delete(item)
    await session.commit()
    return None
