from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.drum_machine_rhythm import DrumMachineRhythm
from app.models.user import User
from app.schemas.drum_machine import DrumMachineRhythmCreate, DrumMachineRhythmOut, DrumMachineRhythmUpdate

router = APIRouter(prefix="/drum-machine/rhythms", tags=["drum-machine"])


@router.get("", response_model=list[DrumMachineRhythmOut])
def list_rhythms(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(DrumMachineRhythm).filter(DrumMachineRhythm.created_by_id == current_user.id).order_by(DrumMachineRhythm.created_at.desc()).all()


@router.post("", response_model=DrumMachineRhythmOut, status_code=status.HTTP_201_CREATED)
def create_rhythm(payload: DrumMachineRhythmCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rhythm = DrumMachineRhythm(**payload.model_dump(), created_by_id=current_user.id)
    db.add(rhythm)
    db.commit()
    db.refresh(rhythm)
    return rhythm


@router.put("/{rhythm_id}", response_model=DrumMachineRhythmOut)
def update_rhythm(rhythm_id: int, payload: DrumMachineRhythmUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rhythm = db.query(DrumMachineRhythm).filter(DrumMachineRhythm.id == rhythm_id, DrumMachineRhythm.created_by_id == current_user.id).first()
    if not rhythm:
        raise HTTPException(status_code=404, detail="Rhythm not found")
    rhythm.name = payload.name
    rhythm.drum_machine = payload.drum_machine
    db.commit()
    db.refresh(rhythm)
    return rhythm
