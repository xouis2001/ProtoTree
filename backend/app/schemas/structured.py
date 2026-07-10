from typing import Any, Literal

from pydantic import BaseModel, Field


class StepItem(BaseModel):
    order: int
    title: str = ""
    content: str = ""
    parameters: dict[str, str] = Field(default_factory=dict)


class StructuredProtocol(BaseModel):
    experiment_name: str = ""
    experiment_type: str = ""
    experiment_subtype: str = ""
    experiment_category: str = ""
    tag_groups: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    content: str = ""
    content_format: Literal["plain", "html"] = "plain"
    steps: list[StepItem] = Field(default_factory=list)


class ProtocolParseRequest(BaseModel):
    raw_text: str = Field(min_length=1)


class ProtocolAssistFormatRequest(BaseModel):
    raw_text: str = Field(min_length=1)
    title_hint: str = ""


class ProtocolParseResponse(BaseModel):
    title: str
    abstract: str
    structured: StructuredProtocol
    parser: str
    warnings: list[str] = Field(default_factory=list)


STRUCTURED_PROTOCOL_JSON_SCHEMA: dict[str, Any] = StructuredProtocol.model_json_schema()
