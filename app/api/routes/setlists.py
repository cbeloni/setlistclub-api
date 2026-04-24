from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models.setlist import Setlist, SetlistItem
from app.models.user import User
from app.schemas.setlist import ReorderSetlistRequest, SetlistCreate, SetlistItemCreate, SetlistOut

router = APIRouter(prefix="/setlists", tags=["setlists"])


@router.get("", response_model=list[SetlistOut])
def list_setlists(db: Session = Depends(get_db)) -> list[Setlist]:
    return (
        db.query(Setlist)
        .options(joinedload(Setlist.items))
        .order_by(Setlist.created_at.desc())
        .all()
    )


@router.get("/{setlist_id}", response_model=SetlistOut)
def get_setlist(setlist_id: int, db: Session = Depends(get_db)) -> Setlist:
    setlist = (
        db.query(Setlist)
        .options(joinedload(Setlist.items))
        .filter(Setlist.id == setlist_id)
        .first()
    )
    if not setlist:
        raise HTTPException(status_code=404, detail="Setlist not found")
    return setlist


@router.post("", response_model=SetlistOut, status_code=status.HTTP_201_CREATED)
def create_setlist(
    payload: SetlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Setlist:
    setlist = Setlist(**payload.model_dump(), created_by_id=current_user.id)
    db.add(setlist)
    db.commit()
    db.refresh(setlist)
    return setlist


@router.post("/{setlist_id}/items", response_model=SetlistOut)
def add_song_to_setlist(
    setlist_id: int,
    payload: SetlistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Setlist:
    setlist = db.query(Setlist).filter(Setlist.id == setlist_id).first()
    if not setlist:
        raise HTTPException(status_code=404, detail="Setlist not found")
    if setlist.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    position = len(setlist.items)
    item = SetlistItem(setlist_id=setlist.id, chord_sheet_id=payload.chord_sheet_id, position=position)
    db.add(item)
    db.commit()

    updated = (
        db.query(Setlist)
        .options(joinedload(Setlist.items))
        .filter(Setlist.id == setlist_id)
        .first()
    )
    return updated


@router.put("/{setlist_id}/reorder", response_model=SetlistOut)
def reorder_setlist(
    setlist_id: int,
    payload: ReorderSetlistRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Setlist:
    setlist = (
        db.query(Setlist)
        .options(joinedload(Setlist.items))
        .filter(Setlist.id == setlist_id)
        .first()
    )
    if not setlist:
        raise HTTPException(status_code=404, detail="Setlist not found")
    if setlist.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    existing_ids = {item.id for item in setlist.items}
    incoming_ids = set(payload.ordered_item_ids)
    if existing_ids != incoming_ids:
        raise HTTPException(status_code=400, detail="ordered_item_ids must contain all and only existing setlist item IDs")

    index_map = {item_id: idx for idx, item_id in enumerate(payload.ordered_item_ids)}
    for item in setlist.items:
        item.position = index_map[item.id]

    db.commit()
    db.refresh(setlist)
    return setlist
