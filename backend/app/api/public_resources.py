import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.resource import AgentSkillResource, AnalysisToolResource, ImageMacroResource
from app.models.user import User
from app.schemas.public_resource import AgentSkillRead, AnalysisToolRead, MacroResourceCreate, MacroResourceRead, MacroResourceUpdate

router = APIRouter(prefix="/public-resources", tags=["public-resources"])


def resource_root() -> Path:
    path = Path(settings.storage_dir) / "public_resources"
    path.mkdir(parents=True, exist_ok=True)
    return path


def tool_root() -> Path:
    path = resource_root() / "analysis_tools"
    path.mkdir(parents=True, exist_ok=True)
    return path


def agent_skill_file_root() -> Path:
    path = resource_root() / "agent_skills"
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(filename: str) -> str:
    stem = Path(filename).stem or "analysis_tool"
    suffix = Path(filename).suffix or ""
    cleaned = re.sub(r"[^\w\-.\u4e00-\u9fff]+", "_", stem, flags=re.UNICODE).strip("._")
    return f"{cleaned or 'analysis_tool'}{suffix}"


def can_write_resource(author_id: int | None, current_user: User) -> bool:
    return current_user.is_admin or author_id == current_user.id


def to_macro_read(item: ImageMacroResource) -> MacroResourceRead:
    return MacroResourceRead.model_validate(item)


def to_tool_read(item: AnalysisToolResource) -> AnalysisToolRead:
    return AnalysisToolRead(
        id=item.id,
        title=item.title,
        description=item.description,
        filename=item.original_filename,
        file_size=item.file_size,
        author_id=item.author_id,
        author_name=item.author_name,
        download_url=f"/public-resources/analysis-tools/{item.id}/download",
        created_at=item.created_at,
    )


def to_agent_skill_read(item: AgentSkillResource) -> AgentSkillRead:
    return AgentSkillRead(
        id=item.id,
        title=item.title,
        description=item.description,
        source_model=item.source_model,
        source_agent=item.source_agent,
        content=item.content,
        filename=item.original_filename,
        file_size=item.file_size,
        author_id=item.author_id,
        author_name=item.author_name,
        download_url=f"/public-resources/agent-skills/{item.id}/download",
        created_at=item.created_at,
    )


@router.get("/image-macros", response_model=list[MacroResourceRead])
async def list_image_macros(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(ImageMacroResource).order_by(ImageMacroResource.created_at.desc()))
    return [to_macro_read(item) for item in result.scalars().all()]


@router.post("/image-macros", response_model=MacroResourceRead, status_code=status.HTTP_201_CREATED)
async def create_image_macro(
    payload: MacroResourceCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    title = payload.title.strip()
    code = payload.code.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Macro code is required")
    item = ImageMacroResource(
        id=uuid4().hex,
        title=title,
        description=payload.description.strip(),
        code=code,
        author_id=current_user.id,
        author_name=current_user.name,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return to_macro_read(item)


@router.put("/image-macros/{macro_id}", response_model=MacroResourceRead)
async def update_image_macro(
    macro_id: str,
    payload: MacroResourceUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = await session.get(ImageMacroResource, macro_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image macro not found")
    if not can_write_resource(item.author_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the uploader or an admin can update this macro")
    title = payload.title.strip()
    code = payload.code.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Macro code is required")
    item.title = title
    item.description = payload.description.strip()
    item.code = code
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return to_macro_read(item)


@router.delete("/image-macros/{macro_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image_macro(
    macro_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = await session.get(ImageMacroResource, macro_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image macro not found")
    if not can_write_resource(item.author_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the uploader or an admin can delete this macro")
    await session.delete(item)
    await session.commit()
    return None


@router.get("/analysis-tools", response_model=list[AnalysisToolRead])
async def list_analysis_tools(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(AnalysisToolResource).order_by(AnalysisToolResource.created_at.desc()))
    return [to_tool_read(item) for item in result.scalars().all()]


@router.post("/analysis-tools", response_model=AnalysisToolRead, status_code=status.HTTP_201_CREATED)
async def upload_analysis_tool(
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required")
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please choose a file")
    tool_id = uuid4().hex
    stored_filename = f"{tool_id}_{safe_filename(file.filename)}"
    path = tool_root() / stored_filename
    size = 0
    with path.open("wb") as output:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            output.write(chunk)
    if size == 0:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    item = AnalysisToolResource(
        id=tool_id,
        title=title.strip(),
        description=description.strip(),
        filename=stored_filename,
        original_filename=file.filename,
        file_size=size,
        author_id=current_user.id,
        author_name=current_user.name,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return to_tool_read(item)


@router.put("/analysis-tools/{tool_id}", response_model=AnalysisToolRead)
async def update_analysis_tool(
    tool_id: str,
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile | None = File(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = await session.get(AnalysisToolResource, tool_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis tool not found")
    if not can_write_resource(item.author_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the uploader or an admin can update this tool")
    if not title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required")
    item.title = title.strip()
    item.description = description.strip()
    if file is not None and file.filename:
        stored_filename = f"{item.id}_{safe_filename(file.filename)}"
        path = tool_root() / stored_filename
        size = 0
        with path.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                output.write(chunk)
        if size == 0:
            path.unlink(missing_ok=True)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
        old_path = tool_root() / item.filename
        item.filename = stored_filename
        item.original_filename = file.filename
        item.file_size = size
        old_path.unlink(missing_ok=True)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return to_tool_read(item)


@router.delete("/analysis-tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis_tool(
    tool_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = await session.get(AnalysisToolResource, tool_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis tool not found")
    if not can_write_resource(item.author_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the uploader or an admin can delete this tool")
    path = tool_root() / item.filename
    path.unlink(missing_ok=True)
    await session.delete(item)
    await session.commit()
    return None


@router.get("/analysis-tools/{tool_id}/download")
async def download_analysis_tool(
    tool_id: str,
    session: AsyncSession = Depends(get_session),
):
    item = await session.get(AnalysisToolResource, tool_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis tool not found")
    path = tool_root() / item.filename
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(path, filename=item.original_filename)


@router.get("/agent-skills", response_model=list[AgentSkillRead])
async def list_agent_skills(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(AgentSkillResource).order_by(AgentSkillResource.created_at.desc()))
    return [to_agent_skill_read(item) for item in result.scalars().all()]


@router.delete("/agent-skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_skill(
    skill_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = await session.get(AgentSkillResource, skill_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent skill not found")
    if not can_write_resource(item.author_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the uploader or an admin can delete this skill")
    path = agent_skill_file_root() / item.filename
    path.unlink(missing_ok=True)
    await session.delete(item)
    await session.commit()
    return None


@router.get("/agent-skills/{skill_id}/download")
async def download_agent_skill(
    skill_id: str,
    session: AsyncSession = Depends(get_session),
):
    item = await session.get(AgentSkillResource, skill_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent skill not found")
    path = agent_skill_file_root() / item.filename
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(path, filename=item.original_filename)


@router.put("/agent-skills/{skill_id}", response_model=AgentSkillRead)
async def update_agent_skill(
    skill_id: str,
    title: str = Form(...),
    description: str = Form(""),
    source_model: str = Form(...),
    source_agent: str = Form(...),
    file: UploadFile | None = File(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = await session.get(AgentSkillResource, skill_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent skill not found")
    if not can_write_resource(item.author_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the uploader or an admin can update this skill")
    title = title.strip()
    source_model = source_model.strip()
    source_agent = source_agent.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent skill title is required")
    if not source_model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source model is required")
    if not source_agent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source agent is required")
    item.title = title
    item.description = description.strip()
    item.source_model = source_model
    item.source_agent = source_agent
    if file is not None and file.filename:
        stored_filename = f"{item.id}_{safe_filename(file.filename)}"
        path = agent_skill_file_root() / stored_filename
        content_bytes = await file.read()
        if not content_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent skill file cannot be empty")
        path.write_bytes(content_bytes)
        old_path = agent_skill_file_root() / item.filename
        try:
            item.content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            item.content = f"Uploaded file: {file.filename}"
        item.filename = stored_filename
        item.original_filename = file.filename
        item.file_size = len(content_bytes)
        old_path.unlink(missing_ok=True)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return to_agent_skill_read(item)


@router.post("/agent-skills", response_model=AgentSkillRead, status_code=status.HTTP_201_CREATED)
async def create_agent_skill(
    title: str = Form(...),
    description: str = Form(""),
    source_model: str = Form(...),
    source_agent: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    title = title.strip()
    source_model = source_model.strip()
    source_agent = source_agent.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent skill title is required")
    if not source_model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source model is required")
    if not source_agent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source agent is required")
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload an agent skill file")
    skill_id = uuid4().hex
    stored_filename = f"{skill_id}_{safe_filename(file.filename)}"
    path = agent_skill_file_root() / stored_filename
    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent skill file cannot be empty")
    path.write_bytes(content_bytes)
    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = f"Uploaded file: {file.filename}"
    item = AgentSkillResource(
        id=skill_id,
        title=title,
        description=description.strip(),
        source_model=source_model,
        source_agent=source_agent,
        content=content,
        filename=stored_filename,
        original_filename=file.filename,
        file_size=len(content_bytes),
        author_id=current_user.id,
        author_name=current_user.name,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return to_agent_skill_read(item)
