from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TaxonomySource(StrEnum):
    official = "official"
    user = "user"
    community = "community"


class TaxonomyStatus(StrEnum):
    active = "active"
    merged = "merged"
    disabled = "disabled"


class ProtocolCategory(Base):
    __tablename__ = "protocol_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    color: Mapped[str] = mapped_column(String(40), default="#2563eb", nullable=False)
    source: Mapped[TaxonomySource] = mapped_column(Enum(TaxonomySource, name="taxonomy_source", values_callable=lambda values: [item.value for item in values]), default=TaxonomySource.official, nullable=False)
    status: Mapped[TaxonomyStatus] = mapped_column(Enum(TaxonomyStatus, name="taxonomy_status", values_callable=lambda values: [item.value for item in values]), default=TaxonomyStatus.active, nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tag_groups = relationship("ProtocolTagGroup", back_populates="category", cascade="all, delete-orphan")


class ProtocolTagGroup(Base):
    __tablename__ = "protocol_tag_groups"
    __table_args__ = (UniqueConstraint("category_id", "normalized_name", name="uq_protocol_tag_group_category_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("protocol_categories.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source: Mapped[TaxonomySource] = mapped_column(Enum(TaxonomySource, name="taxonomy_source", values_callable=lambda values: [item.value for item in values]), default=TaxonomySource.user, nullable=False)
    status: Mapped[TaxonomyStatus] = mapped_column(Enum(TaxonomyStatus, name="taxonomy_status", values_callable=lambda values: [item.value for item in values]), default=TaxonomyStatus.active, nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    merged_into_id: Mapped[int | None] = mapped_column(ForeignKey("protocol_tag_groups.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    category = relationship("ProtocolCategory", back_populates="tag_groups")
    tags = relationship("ProtocolTag", back_populates="tag_group", cascade="all, delete-orphan")


class ProtocolTag(Base):
    __tablename__ = "protocol_tags"
    __table_args__ = (UniqueConstraint("category_id", "tag_group_id", "normalized_name", name="uq_protocol_tag_group_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("protocol_categories.id", ondelete="CASCADE"), index=True, nullable=False)
    tag_group_id: Mapped[int] = mapped_column(ForeignKey("protocol_tag_groups.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source: Mapped[TaxonomySource] = mapped_column(Enum(TaxonomySource, name="taxonomy_source", values_callable=lambda values: [item.value for item in values]), default=TaxonomySource.user, nullable=False)
    status: Mapped[TaxonomyStatus] = mapped_column(Enum(TaxonomyStatus, name="taxonomy_status", values_callable=lambda values: [item.value for item in values]), default=TaxonomyStatus.active, nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    merged_into_id: Mapped[int | None] = mapped_column(ForeignKey("protocol_tags.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tag_group = relationship("ProtocolTagGroup", back_populates="tags")
