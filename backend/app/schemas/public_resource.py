from datetime import datetime

from pydantic import BaseModel


class MacroResourceCreate(BaseModel):
    title: str
    description: str = ""
    code: str


class MacroResourceUpdate(BaseModel):
    title: str
    description: str = ""
    code: str


class MacroResourceRead(BaseModel):
    id: str
    title: str
    description: str
    code: str
    author_id: int | None
    author_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisToolRead(BaseModel):
    id: str
    title: str
    description: str
    filename: str
    file_size: int
    author_id: int | None
    author_name: str
    download_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentSkillRead(BaseModel):
    id: str
    title: str
    description: str
    source_model: str
    source_agent: str
    content: str
    filename: str
    file_size: int
    author_id: int | None
    author_name: str
    download_url: str
    created_at: datetime

    model_config = {"from_attributes": True}
