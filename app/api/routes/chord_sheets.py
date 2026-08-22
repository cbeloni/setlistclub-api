import time
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload, load_only

from app.api.deps import get_current_user, get_current_user_optional, get_db
from app.core.config import settings
from app.db.session import redis_client, redis_sync_client
from app.models.chord_sheet import ChordSheet
from app.models.shared_resource import SharedResource
from app.models.user import User
from app.schemas.chord_sheet import (
    ChordSheetCreate,
    ChordSheetListOut,
    ChordSheetOut,
    ChordSheetScrollSpeedUpdate,
    ChordSheetUpdate,
)
from app.services.sharing import (
    can_modify_chord_sheet,
    get_shared_resource_ids,
    list_shared_users,
    share_resource,
    unshare_resource,
)

router = APIRouter(prefix="/chord-sheets", tags=["chord-sheets"])

RECENT_VIEWS_MAX = 50
RECENT_VIEWS_TTL = 60 * 60 * 24 * 30  # 30 days
TAB_VISIBILITY_TTL = 60 * 60 * 24 * 365  # 1 year


class TabVisibilityUpdate(BaseModel):
    tab_hidden: bool


class ShareRequest(BaseModel):
    email: str


class SharedUserOut(BaseModel):
    id: int
    email: str
    display_name: str


def _enrich_sheet(sheet: ChordSheet, schema=ChordSheetOut):
    data = schema.model_validate(sheet)
    data.created_by_name = sheet.created_by.display_name if sheet.created_by else None
    view_count = redis_sync_client.get(f"views:chord_sheet:{sheet.id}")
    data.view_count = int(view_count or 0)
    data.share_url = f"{settings.BASE_URL}/c/{sheet.share_token}"
    return data


def _can_modify_sheet(sheet, current_user: User, db: Session) -> bool:
    """Check permission: owner or shared user."""
    return can_modify_chord_sheet(sheet, current_user, db)


def _list_columns():
    return load_only(
        ChordSheet.id,
        ChordSheet.title,
        ChordSheet.artist,
        ChordSheet.key_signature,
        ChordSheet.scroll_speed,
        ChordSheet.is_private,
        ChordSheet.created_by_id,
        ChordSheet.created_at,
        ChordSheet.share_token,
    )


@router.get("", response_model=list[ChordSheetListOut])
def list_chord_sheets(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[ChordSheetListOut]:
    """List chord sheets: public + own private + shared with me."""
    query = db.query(ChordSheet).options(_list_columns(), joinedload(ChordSheet.created_by)).filter(ChordSheet.is_private == False)
    if current_user:
        shared_ids = get_shared_resource_ids("chord_sheet", current_user.id, db)
        query = query.filter(
            (ChordSheet.is_private == False)
            | (ChordSheet.created_by_id == current_user.id)
            | (ChordSheet.id.in_(shared_ids))
        )
    else:
        query = query.filter(ChordSheet.is_private == False)
    sheets = query.order_by(ChordSheet.created_at.desc()).all()
    return [_enrich_sheet(s, ChordSheetListOut) for s in sheets]


@router.get("/share/{share_token}", response_model=ChordSheetOut)
def get_chord_sheet_by_token(share_token: str, db: Session = Depends(get_db)) -> ChordSheetOut:
    sheet = (
        db.query(ChordSheet)
        .options(joinedload(ChordSheet.created_by))
        .filter(ChordSheet.share_token == share_token)
        .first()
    )
    if not sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")
    return _enrich_sheet(sheet)


@router.get("/recently-viewed", response_model=list[ChordSheetListOut])
async def list_recently_viewed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChordSheetListOut]:
    key = f"recent:{current_user.id}"
    member_scores = await redis_client.zrevrange(key, 0, RECENT_VIEWS_MAX - 1, withscores=True)
    if not member_scores:
        return []
    chord_sheets = []
    for member_id, _ in member_scores:
        sheet = (
            db.query(ChordSheet)
            .options(_list_columns(), joinedload(ChordSheet.created_by))
            .filter(ChordSheet.id == int(member_id))
            .first()
        )
        if sheet:
            chord_sheets.append(sheet)
    return [_enrich_sheet(s, ChordSheetListOut) for s in chord_sheets]


@router.get("/{chord_sheet_id}", response_model=ChordSheetOut)
def get_chord_sheet(chord_sheet_id: int, db: Session = Depends(get_db)) -> ChordSheetOut:
    sheet = (
        db.query(ChordSheet)
        .options(joinedload(ChordSheet.created_by))
        .filter(ChordSheet.id == chord_sheet_id)
        .first()
    )
    if not sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")
    return _enrich_sheet(sheet)


# === Sharing Endpoints ===

@router.post("/{chord_sheet_id}/share", response_model=SharedUserOut)
def share_chord_sheet(
    chord_sheet_id: int,
    payload: ShareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    sheet = db.query(ChordSheet).filter(ChordSheet.id == chord_sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")
    if not _can_modify_sheet(sheet, current_user, db):
        raise HTTPException(status_code=403, detail="Not allowed")
    return share_resource("chord_sheet", chord_sheet_id, payload.email, current_user, db)


@router.delete("/{chord_sheet_id}/share/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unshare_chord_sheet(
    chord_sheet_id: int,
    target_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sheet = db.query(ChordSheet).filter(ChordSheet.id == chord_sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")
    if sheet.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can remove sharing")
    unshare_resource("chord_sheet", chord_sheet_id, target_user_id, current_user, db)


@router.get("/{chord_sheet_id}/shared-users", response_model=list[SharedUserOut])
def list_chord_sheet_shared_users(
    chord_sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    sheet = db.query(ChordSheet).filter(ChordSheet.id == chord_sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")
    if not _can_modify_sheet(sheet, current_user, db):
        raise HTTPException(status_code=403, detail="Not allowed")
    return list_shared_users("chord_sheet", chord_sheet_id, db)


@router.get("/shared-with-me", response_model=list[ChordSheetListOut])
def list_chord_sheets_shared_with_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChordSheetListOut]:
    shared_ids = get_shared_resource_ids("chord_sheet", current_user.id, db)
    sheets = (
        db.query(ChordSheet)
        .options(_list_columns(), joinedload(ChordSheet.created_by))
        .filter(ChordSheet.id.in_(shared_ids))
        .order_by(ChordSheet.created_at.desc())
        .all()
    )
    return [_enrich_sheet(s, ChordSheetListOut) for s in sheets]


@router.post("/{chord_sheet_id}/view", status_code=status.HTTP_204_NO_CONTENT)
async def record_chord_sheet_view(
    chord_sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> None:
    sheet = db.query(ChordSheet).filter(ChordSheet.id == chord_sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")

    await redis_client.incr(f"views:chord_sheet:{chord_sheet_id}")

    if current_user:
        key = f"recent:{current_user.id}"
        now = time.time()
        await redis_client.zadd(key, {str(chord_sheet_id): now})
        await redis_client.zremrangebyrank(key, 0, -(RECENT_VIEWS_MAX + 1))
        await redis_client.expire(key, RECENT_VIEWS_TTL)


@router.get("/{chord_sheet_id}/tab-visibility", response_model=TabVisibilityUpdate)
async def get_tab_visibility(
    chord_sheet_id: int,
    current_user: User = Depends(get_current_user),
) -> TabVisibilityUpdate:
    key = f"tab:{current_user.id}:{chord_sheet_id}"
    value = await redis_client.get(key)
    if value is None:
        return TabVisibilityUpdate(tab_hidden=True)
    return TabVisibilityUpdate(tab_hidden=value == "1")


@router.put("/{chord_sheet_id}/tab-visibility", status_code=status.HTTP_204_NO_CONTENT)
async def set_tab_visibility(
    chord_sheet_id: int,
    payload: TabVisibilityUpdate,
    current_user: User = Depends(get_current_user),
) -> None:
    key = f"tab:{current_user.id}:{chord_sheet_id}"
    await redis_client.setex(key, TAB_VISIBILITY_TTL, "1" if payload.tab_hidden else "0")


@router.post("", response_model=ChordSheetOut, status_code=status.HTTP_201_CREATED)
def create_chord_sheet(
    payload: ChordSheetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChordSheetOut:
    chord_sheet = ChordSheet(
        **payload.model_dump(exclude={"is_private", "image_data"}),
        image_data=json.dumps(payload.image_data) if payload.image_data else None,
        is_private=payload.is_private,
        share_token=str(uuid.uuid4()),
        created_by_id=current_user.id,
    )
    db.add(chord_sheet)
    db.commit()
    db.refresh(chord_sheet)
    return _enrich_sheet(chord_sheet)


@router.put("/{chord_sheet_id}", response_model=ChordSheetOut)
def update_chord_sheet(
    chord_sheet_id: int,
    payload: ChordSheetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChordSheetOut:
    chord_sheet = db.query(ChordSheet).filter(ChordSheet.id == chord_sheet_id).first()
    if not chord_sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")
    if not _can_modify_sheet(chord_sheet, current_user, db):
        raise HTTPException(status_code=403, detail="Not allowed")

    update_data = payload.model_dump(exclude_unset=True)
    if "image_data" in update_data:
        update_data["image_data"] = json.dumps(update_data["image_data"]) if update_data["image_data"] else None
    if "is_private" in update_data and chord_sheet.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can change privacy")
    for key, value in update_data.items():
        setattr(chord_sheet, key, value)

    db.commit()
    db.refresh(chord_sheet)
    return _enrich_sheet(chord_sheet)


@router.put("/{chord_sheet_id}/scroll-speed", response_model=ChordSheetOut)
def update_chord_sheet_scroll_speed(
    chord_sheet_id: int,
    payload: ChordSheetScrollSpeedUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChordSheetOut:
    chord_sheet = db.query(ChordSheet).filter(ChordSheet.id == chord_sheet_id).first()
    if not chord_sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")

    chord_sheet.scroll_speed = payload.scroll_speed
    db.commit()
    db.refresh(chord_sheet)
    return _enrich_sheet(chord_sheet)


@router.delete("/{chord_sheet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chord_sheet(
    chord_sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chord_sheet = db.query(ChordSheet).filter(ChordSheet.id == chord_sheet_id).first()
    if not chord_sheet:
        raise HTTPException(status_code=404, detail="Chord sheet not found")
    if not _can_modify_sheet(chord_sheet, current_user, db):
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(chord_sheet)
    db.commit()
    return None
