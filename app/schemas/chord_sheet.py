from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ChordSheetBase(BaseModel):
    title: str
    artist: str
    key_signature: str | None = None
    content: str
    youtube_url: HttpUrl | None = None
    scroll_speed: float = Field(default=1.0, ge=0.2, le=1.8)


class ChordSheetCreate(ChordSheetBase):
    pass


class ChordSheetUpdate(ChordSheetBase):
    pass


class ChordSheetScrollSpeedUpdate(BaseModel):
    scroll_speed: float = Field(ge=0.2, le=1.8)


class ChordSheetOut(ChordSheetBase):
    id: int
    created_by_id: int
    created_at: datetime

    class Config:
        from_attributes = True
