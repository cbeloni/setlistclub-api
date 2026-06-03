import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.session import redis_client
from app.models.chord_sheet import ChordSheet
from app.models.user import User
from app.schemas.chord_sheet import (
    ChordSheetCreate,
    ChordSheetOut,
    ChordSheetScrollSpeedUpdate,
    ChordSheetUpdate,
)

router = APIRouter(prefix="/chord-sheets", tags=["chord-sheets"])

RECENT_VIEWS_MAX = 50
RECENT_VIEWS_TTL = 60 * 60 * 24 * 30  # 30 days


@router.get("", response_model=list[ChordSheetOut])
def list_chord_sheets(db: Session = Depends(get_db)) -> list[ChordSheet]:
    return db.query(ChordSheet).order_by(ChordSheet.created_at.desc()).all()


@router.get("/recently-viewed", response_model=list[ChordSheetOut])
async def list_recently_viewed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChordSheet]:
    key = f"recent:{current_user.id}"
    # Busca os IDs ordenados por score descendente
    member_scores = await redis_client.zrevrange(key, 0, RECENT_VIEWS_MAX - 1, withscores=True)
    if not member_scores:
        return []

    chord_sheets = []
    for member_id, _ in member_scores:
        sheet = db.query(ChordSheet).filter(ChordSheet.id == int(member_id)).first()
        if sheet:
            chord_sheets.append(sheet)

    return chord_sheets


@router.get("/{chord_sheet_id}", response_model=ChordSheetOut)
def get_chord_sheet(chord_sheet_id: int, db: Session = Depends(get_db)) -> ChordSheet:
    chord_sheet = db.query(ChordSheet).filter(ChordSheet.id == chord_sheet_id).first()
    if not chord_sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")
    return chord_sheet


@router.post("/{chord_sheet_id}/view", status_code=status.HTTP_204_NO_CONTENT)
async def record_chord_sheet_view(
    chord_sheet_id: int,
    current_user: User = Depends(get_current_user),
) -> None:
    key = f"recent:{current_user.id}"
    now = time.time()
    # Adiciona/atualiza o member com o timestamp atual como score
    await redis_client.zadd(key, {str(chord_sheet_id): now})
    # Mantém apenas os RECENT_VIEWS_MAX mais recentes
    await redis_client.zremrangebyrank(key, 0, -(RECENT_VIEWS_MAX + 1))
    # Atualiza o TTL da chave
    await redis_client.expire(key, RECENT_VIEWS_TTL)


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

    for key, value in payload.model_dump().items():
        setattr(chord_sheet, key, value)

    db.commit()
    db.refresh(chord_sheet)
    return chord_sheet


@router.put("/{chord_sheet_id}/scroll-speed", response_model=ChordSheetOut)
def update_chord_sheet_scroll_speed(
    chord_sheet_id: int,
    payload: ChordSheetScrollSpeedUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChordSheet:
    chord_sheet = db.query(ChordSheet).filter(ChordSheet.id == chord_sheet_id).first()
    if not chord_sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")

    chord_sheet.scroll_speed = payload.scroll_speed
    db.commit()
    db.refresh(chord_sheet)
    return chord_sheet


@router.delete("/{chord_sheet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chord_sheet(
    chord_sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chord_sheet = db.query(ChordSheet).filter(ChordSheet.id == chord_sheet_id).first()
    if not chord_sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")
    if chord_sheet.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(chord_sheet)
    db.commit()
    return None