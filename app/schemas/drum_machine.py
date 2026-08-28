from datetime import datetime

from pydantic import BaseModel, Field


class DrumMachineRhythmCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    drum_machine: str = Field(min_length=1, max_length=2048)


class DrumMachineRhythmUpdate(DrumMachineRhythmCreate):
    pass


class DrumMachineRhythmOut(DrumMachineRhythmCreate):
    id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
