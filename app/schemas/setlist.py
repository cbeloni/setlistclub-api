from datetime import datetime

from pydantic import BaseModel


class SetlistCreate(BaseModel):
    name: str
    description: str | None = None


class SetlistItemCreate(BaseModel):
    chord_sheet_id: int


class ReorderSetlistRequest(BaseModel):
    ordered_item_ids: list[int]


class SetlistItemOut(BaseModel):
    id: int
    position: int
    chord_sheet_id: int

    class Config:
        from_attributes = True


class SetlistOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_by_id: int
    created_at: datetime
    items: list[SetlistItemOut]

    class Config:
        from_attributes = True
