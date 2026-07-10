from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProtocolVisibility(StrEnum):
    public = "public"
    private = "private"


class ProtocolSource(StrEnum):
    user = "user"
    base = "base"


class Protocol(Base):
    __tablename__ = "protocols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    root_id: Mapped[int | None] = mapped_column(ForeignKey("protocols.id", ondelete="SET NULL"), nullable=True, index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("protocols.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    abstract: Mapped[str] = mapped_column(Text, default="", nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    folder_id: Mapped[int | None] = mapped_column(ForeignKey("protocol_folders.id", ondelete="SET NULL"), index=True, nullable=True)
    source: Mapped[ProtocolSource] = mapped_column(Enum(ProtocolSource, name="protocol_source", values_callable=lambda values: [item.value for item in values]), default=ProtocolSource.user, nullable=False)
    visibility: Mapped[ProtocolVisibility] = mapped_column(Enum(ProtocolVisibility, name="protocol_visibility", values_callable=lambda values: [item.value for item in values]), default=ProtocolVisibility.public, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    structured: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    version_label: Mapped[str] = mapped_column(String(40), default="v1.0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    author = relationship("User", back_populates="protocols")
    folder = relationship("ProtocolFolder", back_populates="protocols")
    stars = relationship("ProtocolStar", back_populates="protocol")
