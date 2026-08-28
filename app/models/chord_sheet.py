import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChordSheet(Base):
    __tablename__ = "chord_sheets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    artist: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    key_signature: Mapped[str | None] = mapped_column(String(16), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_data: Mapped[str | None] = mapped_column(LONGTEXT, nullable=True)
    is_bucket_storage: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    youtube_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    drum_machine: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    scroll_speed: Mapped[float] = mapped_column(Float, nullable=False, server_default="1.0")
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    share_token: Mapped[str] = mapped_column(
        String(64), nullable=False, default=lambda: str(uuid.uuid4()), index=True
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    created_by = relationship("User", back_populates="chord_sheets")
    setlist_items = relationship("SetlistItem", back_populates="chord_sheet", cascade="all, delete-orphan")
