from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProtocolStar(Base):
    __tablename__ = "protocol_stars"
    __table_args__ = (UniqueConstraint("protocol_id", "user_id", name="uq_protocol_star_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    protocol_id: Mapped[int] = mapped_column(ForeignKey("protocols.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    protocol = relationship("Protocol", back_populates="stars")
    user = relationship("User")


class CommercialProtocolStar(Base):
    __tablename__ = "commercial_protocol_stars"
    __table_args__ = (UniqueConstraint("commercial_protocol_id", "user_id", name="uq_commercial_protocol_star_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    commercial_protocol_id: Mapped[str] = mapped_column(ForeignKey("commercial_protocol_resources.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    commercial_protocol = relationship("CommercialProtocolResource")
    user = relationship("User")
