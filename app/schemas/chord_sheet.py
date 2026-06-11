from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ChordSheetBase(BaseModel):
    title: str
    artist: str
    key_signature: str | None = None
    content: str
    youtube_url: HttpUrl | None = None
    scroll_speed: float = Field(default=1.0, ge=0.2, le=1.8)
    is_private: bool = False


class ChordSheetCreate(ChordSheetBase):
    pass


class ChordSheetUpdate(ChordSheetBase):
    pass


class ChordSheetScrollSpeedUpdate(BaseModel):
    scroll_speed: float = Field(ge=0.2, le=1.8)


class ChordSheetOut(ChordSheetBase):
    id: int
    created_by_id: int
    created_by_name: str | None = None
    created_at: datetime
    view_count: int = 0
    is_private: bool
    share_token: str
    share_url: str | None = None

    class Config:
        from_attributes = True
