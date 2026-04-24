from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Setlist(Base):
    __tablename__ = "setlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    created_by = relationship("User", back_populates="setlists")
    items = relationship("SetlistItem", back_populates="setlist", cascade="all, delete-orphan", order_by="SetlistItem.position")


class SetlistItem(Base):
    __tablename__ = "setlist_items"
    __table_args__ = (UniqueConstraint("setlist_id", "position", name="uq_setlist_position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    setlist_id: Mapped[int] = mapped_column(ForeignKey("setlists.id", ondelete="CASCADE"), nullable=False, index=True)
    chord_sheet_id: Mapped[int] = mapped_column(ForeignKey("chord_sheets.id", ondelete="CASCADE"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    setlist = relationship("Setlist", back_populates="items")
    chord_sheet = relationship("ChordSheet", back_populates="setlist_items")
