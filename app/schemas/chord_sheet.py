from datetime import datetime
import json

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


def _normalize_image_data(value: str | list[str] | None) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        normalized = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        return normalized or None
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        try:
            parsed = json.loads(normalized)
        except json.JSONDecodeError:
            return [normalized]
        if isinstance(parsed, list):
            normalized_list = [item.strip() for item in parsed if isinstance(item, str) and item.strip()]
            return normalized_list or None
        if isinstance(parsed, str) and parsed.strip():
            return [parsed.strip()]
        return None
    return None


class ChordSheetBase(BaseModel):
    title: str
    artist: str
    key_signature: str | None = None
    content: str
    image_data: list[str] | None = None
    youtube_url: HttpUrl | None = None
    scroll_speed: float = Field(default=1.0, ge=0.2, le=1.8)
    is_private: bool = False

    @field_validator("image_data", mode="before")
    @classmethod
    def parse_image_data(cls, value):
        return _normalize_image_data(value)

    @model_validator(mode="after")
    def validate_content_or_image(self):
        if self.image_data:
            for item in self.image_data:
                if not (
                    isinstance(item, str)
                    and (item.startswith("data:image/") or item.startswith("data:application/pdf"))
                ):
                    raise ValueError("image_data deve conter apenas strings data:image/ ou data:application/pdf.")
        if not self.content.strip() and not self.image_data:
            raise ValueError("Adicione a cifra em texto, uma imagem ou um PDF.")
        return self


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
