from datetime import datetime

from pydantic import BaseModel, HttpUrl


class ChordSheetBase(BaseModel):
    title: str
    artist: str
    key_signature: str | None = None
    content: str
    youtube_url: HttpUrl | None = None


class ChordSheetCreate(ChordSheetBase):
    pass


class ChordSheetUpdate(ChordSheetBase):
    pass


class ChordSheetOut(ChordSheetBase):
    id: int
    created_by_id: int
    created_at: datetime

    class Config:
        from_attributes = True
