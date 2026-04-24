from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.chord_sheet import ChordSheet
from app.models.user import User
from app.schemas.chord_sheet import ChordSheetCreate, ChordSheetOut, ChordSheetUpdate

router = APIRouter(prefix="/chord-sheets", tags=["chord-sheets"])


@router.get("", response_model=list[ChordSheetOut])
def list_chord_sheets(db: Session = Depends(get_db)) -> list[ChordSheet]:
    return db.query(ChordSheet).order_by(ChordSheet.created_at.desc()).all()


@router.get("/{chord_sheet_id}", response_model=ChordSheetOut)
def get_chord_sheet(chord_sheet_id: int, db: Session = Depends(get_db)) -> ChordSheet:
    chord_sheet = db.query(ChordSheet).filter(ChordSheet.id == chord_sheet_id).first()
    if not chord_sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")
    return chord_sheet


@router.post("", response_model=ChordSheetOut, status_code=status.HTTP_201_CREATED)
def create_chord_sheet(
    payload: ChordSheetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChordSheet:
    chord_sheet = ChordSheet(**payload.model_dump(), created_by_id=current_user.id)
    db.add(chord_sheet)
    db.commit()
    db.refresh(chord_sheet)
    return chord_sheet


@router.put("/{chord_sheet_id}", response_model=ChordSheetOut)
def update_chord_sheet(
    chord_sheet_id: int,
    payload: ChordSheetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChordSheet:
    chord_sheet = db.query(ChordSheet).filter(ChordSheet.id == chord_sheet_id).first()
    if not chord_sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")
    if chord_sheet.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    for key, value in payload.model_dump().items():
        setattr(chord_sheet, key, value)

    db.commit()
    db.refresh(chord_sheet)
    return chord_sheet
