from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ContributionEventType(StrEnum):
    create_protocol = "create_protocol"
    fork_protocol = "fork_protocol"
    protocol_forked_by_other = "protocol_forked_by_other"
    update_protocol = "update_protocol"
    add_pitfall = "add_pitfall"
    add_comment = "add_comment"
    receive_star = "receive_star"


class ContributionEvent(Base):
    __tablename__ = "contribution_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[ContributionEventType] = mapped_column(Enum(ContributionEventType, name="contribution_event_type", values_callable=lambda values: [item.value for item in values]), index=True, nullable=False)
    score_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    protocol_id: Mapped[int | None] = mapped_column(ForeignKey("protocols.id", ondelete="SET NULL"), index=True, nullable=True)
    related_protocol_id: Mapped[int | None] = mapped_column(ForeignKey("protocols.id", ondelete="SET NULL"), index=True, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="contribution_events")
