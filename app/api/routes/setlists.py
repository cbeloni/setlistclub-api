import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_current_user_optional, get_db
from app.core.config import settings
from app.models.setlist import Setlist, SetlistItem
from app.models.user import User
from app.schemas.setlist import ReorderSetlistRequest, SetlistCreate, SetlistItemCreate, SetlistOut
from app.services.sharing import (
    can_modify_setlist,
    get_shared_resource_ids,
    list_shared_users,
    share_resource,
    unshare_resource,
)

router = APIRouter(prefix="/setlists", tags=["setlists"])


class ShareRequest(BaseModel):
    email: str


class SharedUserOut(BaseModel):
    id: int
    email: str
    display_name: str


def _enrich_setlist(setlist: Setlist) -> SetlistOut:
    data = SetlistOut.model_validate(setlist)
    data.share_url = f"{settings.BASE_URL}/s/{setlist.share_token}"
    return data


def _can_modify_setlist_obj(setlist, current_user: User, db: Session) -> bool:
    return can_modify_setlist(setlist, current_user, db)


@router.get("", response_model=list[SetlistOut])
def list_setlists(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[SetlistOut]:
    query = db.query(Setlist).options(joinedload(Setlist.items).joinedload(SetlistItem.chord_sheet))
    if current_user:
        shared_ids = get_shared_resource_ids("setlist", current_user.id, db)
        query = query.filter(
            (Setlist.is_private == False)
            | (Setlist.created_by_id == current_user.id)
            | (Setlist.id.in_(shared_ids))
        )
    else:
        query = query.filter(Setlist.is_private == False)
    setlists = query.order_by(Setlist.created_at.desc()).all()
    return [_enrich_setlist(s) for s in setlists]


@router.get("/share/{share_token}", response_model=SetlistOut)
def get_setlist_by_token(share_token: str, db: Session = Depends(get_db)) -> SetlistOut:
    setlist = (
        db.query(Setlist)
        .options(joinedload(Setlist.items).joinedload(SetlistItem.chord_sheet))
        .filter(Setlist.share_token == share_token)
        .first()
    )
    if not setlist:
        raise HTTPException(status_code=404, detail="Setlist not found")
    return _enrich_setlist(setlist)


@router.get("/{setlist_id}", response_model=SetlistOut)
def get_setlist(setlist_id: int, db: Session = Depends(get_db)) -> SetlistOut:
    setlist = (
        db.query(Setlist)
        .options(joinedload(Setlist.items).joinedload(SetlistItem.chord_sheet))
        .filter(Setlist.id == setlist_id)
        .first()
    )
    if not setlist:
        raise HTTPException(status_code=404, detail="Setlist not found")
    return _enrich_setlist(setlist)


# === Sharing Endpoints ===

@router.post("/{setlist_id}/share", response_model=SharedUserOut)
def share_setlist(
    setlist_id: int,
    payload: ShareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    setlist = db.query(Setlist).filter(Setlist.id == setlist_id).first()
    if not setlist:
        raise HTTPException(status_code=404, detail="Setlist not found")
    if not _can_modify_setlist_obj(setlist, current_user, db):
        raise HTTPException(status_code=403, detail="Not allowed")
    return share_resource("setlist", setlist_id, payload.email, current_user, db)


@router.delete("/{setlist_id}/share/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unshare_setlist(
    setlist_id: int,
    target_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    setlist = db.query(Setlist).filter(Setlist.id == setlist_id).first()
    if not setlist:
        raise HTTPException(status_code=404, detail="Setlist not found")
    if setlist.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can remove sharing")
    unshare_resource("setlist", setlist_id, target_user_id, current_user, db)


@router.get("/{setlist_id}/shared-users", response_model=list[SharedUserOut])
def list_setlist_shared_users(
    setlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    setlist = db.query(Setlist).filter(Setlist.id == setlist_id).first()
    if not setlist:
        raise HTTPException(status_code=404, detail="Setlist not found")
    if not _can_modify_setlist_obj(setlist, current_user, db):
        raise HTTPException(status_code=403, detail="Not allowed")
    return list_shared_users("setlist", setlist_id, db)


@router.get("/shared-with-me", response_model=list[SetlistOut])
def list_setlists_shared_with_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SetlistOut]:
    shared_ids = get_shared_resource_ids("setlist", current_user.id, db)
    setlists = (
        db.query(Setlist)
        .options(joinedload(Setlist.items).joinedload(SetlistItem.chord_sheet))
        .filter(Setlist.id.in_(shared_ids))
        .order_by(Setlist.created_at.desc())
        .all()
    )
    return [_enrich_setlist(s) for s in setlists]


# === CRUD Endpoints ===

@router.post("", response_model=SetlistOut, status_code=status.HTTP_201_CREATED)
def create_setlist(
    payload: SetlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SetlistOut:
    setlist = Setlist(
        **payload.model_dump(exclude={"is_private"}),
        is_private=payload.is_private,
        share_token=str(uuid.uuid4()),
        created_by_id=current_user.id,
    )
    db.add(setlist)
    db.commit()
    db.refresh(setlist)
    return _enrich_setlist(setlist)


@router.post("/{setlist_id}/items", response_model=SetlistOut)
def add_song_to_setlist(
    setlist_id: int,
    payload: SetlistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SetlistOut:
    setlist = db.query(Setlist).filter(Setlist.id == setlist_id).first()
    if not setlist:
        raise HTTPException(status_code=404, detail="Setlist not found")
    if not _can_modify_setlist_obj(setlist, current_user, db):
        raise HTTPException(status_code=403, detail="Not allowed")

    position = len(setlist.items)
    item = SetlistItem(setlist_id=setlist.id, chord_sheet_id=payload.chord_sheet_id, position=position)
    db.add(item)
    db.commit()

    updated = (
        db.query(Setlist)
        .options(joinedload(Setlist.items).joinedload(SetlistItem.chord_sheet))
        .filter(Setlist.id == setlist_id)
        .first()
    )
    return _enrich_setlist(updated)


@router.put("/{setlist_id}/reorder", response_model=SetlistOut)
def reorder_setlist(
    setlist_id: int,
    payload: ReorderSetlistRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SetlistOut:
    setlist = (
        db.query(Setlist)
        .options(joinedload(Setlist.items).joinedload(SetlistItem.chord_sheet))
        .filter(Setlist.id == setlist_id)
        .first()
    )
    if not setlist:
        raise HTTPException(status_code=404, detail="Setlist not found")
    if not _can_modify_setlist_obj(setlist, current_user, db):
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
    return _enrich_setlist(setlist)


@router.delete("/{setlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_setlist(
    setlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    setlist = db.query(Setlist).filter(Setlist.id == setlist_id).first()
    if not setlist:
        raise HTTPException(status_code=404, detail="Setlist not found")
    if not _can_modify_setlist_obj(setlist, current_user, db):
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(setlist)
    db.commit()
    return None


@router.delete("/{setlist_id}/items/{item_id}", response_model=SetlistOut)
def remove_song_from_setlist(
    setlist_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SetlistOut:
    setlist = (
        db.query(Setlist)
        .options(joinedload(Setlist.items).joinedload(SetlistItem.chord_sheet))
        .filter(Setlist.id == setlist_id)
        .first()
    )
    if not setlist:
        raise HTTPException(status_code=404, detail="Setlist not found")
    if not _can_modify_setlist_obj(setlist, current_user, db):
        raise HTTPException(status_code=403, detail="Not allowed")

    item = db.query(SetlistItem).filter(SetlistItem.id == item_id, SetlistItem.setlist_id == setlist_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Setlist item not found")

    db.delete(item)
    db.commit()

    remaining_items = (
        db.query(SetlistItem)
        .filter(SetlistItem.setlist_id == setlist_id)
        .order_by(SetlistItem.position)
        .all()
    )
    for idx, r_item in enumerate(remaining_items):
        r_item.position = idx

    db.commit()
    db.refresh(setlist)
    return _enrich_setlist(setlist)