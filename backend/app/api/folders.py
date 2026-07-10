from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.folder import ProtocolFolder
from app.models.protocol import Protocol
from app.models.user import User
from app.schemas.folder import ProtocolFolderCreate, ProtocolFolderRead, ProtocolFolderUpdate

router = APIRouter(prefix="/folders", tags=["folders"])


async def get_owned_folder(folder_id: int, session: AsyncSession, current_user: User) -> ProtocolFolder:
    result = await session.execute(select(ProtocolFolder).where(ProtocolFolder.id == folder_id, ProtocolFolder.owner_id == current_user.id))
    folder = result.scalar_one_or_none()
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    return folder


async def validate_parent(parent_id: int | None, session: AsyncSession, current_user: User, folder_id: int | None = None) -> None:
    if parent_id is None:
        return
    if parent_id == folder_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Folder cannot be its own parent")
    parent = await get_owned_folder(parent_id, session, current_user)
    if folder_id is None:
        return
    current = parent
    while current is not None:
        if current.id == folder_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Folder cannot move into its child")
        if current.parent_id is None:
            break
        result = await session.execute(select(ProtocolFolder).where(ProtocolFolder.id == current.parent_id, ProtocolFolder.owner_id == current_user.id))
        current = result.scalar_one_or_none()


async def ensure_unique_sibling_name(name: str, parent_id: int | None, session: AsyncSession, current_user: User, folder_id: int | None = None) -> None:
    stmt = select(ProtocolFolder).where(ProtocolFolder.owner_id == current_user.id, ProtocolFolder.name == name)
    if parent_id is None:
        stmt = stmt.where(ProtocolFolder.parent_id.is_(None))
    else:
        stmt = stmt.where(ProtocolFolder.parent_id == parent_id)
    if folder_id is not None:
        stmt = stmt.where(ProtocolFolder.id != folder_id)
    result = await session.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="同级文件夹名称已存在")


@router.get("", response_model=list[ProtocolFolderRead])
async def list_folders(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(ProtocolFolder).where(ProtocolFolder.owner_id == current_user.id).order_by(ProtocolFolder.created_at.asc(), ProtocolFolder.name.asc()))
    return result.scalars().all()


@router.post("", response_model=ProtocolFolderRead, status_code=status.HTTP_201_CREATED)
async def create_folder(
    payload: ProtocolFolderCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    name = payload.name.strip()
    await validate_parent(payload.parent_id, session, current_user)
    await ensure_unique_sibling_name(name, payload.parent_id, session, current_user)
    folder = ProtocolFolder(owner_id=current_user.id, parent_id=payload.parent_id, name=name)
    session.add(folder)
    await session.commit()
    await session.refresh(folder)
    return folder


@router.put("/{folder_id}", response_model=ProtocolFolderRead)
async def update_folder(
    folder_id: int,
    payload: ProtocolFolderUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    folder = await get_owned_folder(folder_id, session, current_user)
    updates = payload.model_dump(exclude_unset=True)
    next_name = updates["name"].strip() if "name" in updates and updates["name"] is not None else folder.name
    next_parent_id = updates["parent_id"] if "parent_id" in updates else folder.parent_id
    if "parent_id" in updates:
        await validate_parent(next_parent_id, session, current_user, folder_id)
    await ensure_unique_sibling_name(next_name, next_parent_id, session, current_user, folder_id)
    folder.name = next_name
    folder.parent_id = next_parent_id
    await session.commit()
    await session.refresh(folder)
    return folder


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    folder = await get_owned_folder(folder_id, session, current_user)
    child_result = await session.execute(select(ProtocolFolder).where(ProtocolFolder.owner_id == current_user.id, ProtocolFolder.parent_id == folder_id))
    for child in child_result.scalars().all():
        child.parent_id = folder.parent_id
        session.add(child)
    protocol_result = await session.execute(select(Protocol).where(Protocol.author_id == current_user.id, Protocol.folder_id == folder_id))
    for protocol in protocol_result.scalars().all():
        protocol.folder_id = None
        session.add(protocol)
    await session.delete(folder)
    await session.commit()
    return None
