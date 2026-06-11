from sqlalchemy.orm import Session

from app.models.shared_resource import SharedResource
from app.models.user import User


def can_modify_chord_sheet(chord_sheet, current_user: User, db: Session) -> bool:
    """Check if user can modify (edit/delete) a chord sheet."""
    return _can_modify("chord_sheet", chord_sheet, current_user, db)


def can_modify_setlist(setlist, current_user: User, db: Session) -> bool:
    """Check if user can modify (edit/delete) a setlist."""
    return _can_modify("setlist", setlist, current_user, db)


def _can_modify(resource_type: str, resource, current_user: User, db: Session) -> bool:
    if resource.created_by_id == current_user.id:
        return True
    share = db.query(SharedResource).filter(
        SharedResource.resource_type == resource_type,
        SharedResource.resource_id == resource.id,
        SharedResource.shared_with_user_id == current_user.id,
    ).first()
    return share is not None


def share_resource(
    resource_type: str,
    resource_id: int,
    email: str,
    current_user: User,
    db: Session,
) -> dict:
    """Share a resource with a user by email. Returns the user info or raises."""
    from fastapi import HTTPException, status

    target_user = db.query(User).filter(User.email == email).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found",
        )
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot share with yourself",
        )

    existing = db.query(SharedResource).filter(
        SharedResource.resource_type == resource_type,
        SharedResource.resource_id == resource_id,
        SharedResource.shared_with_user_id == target_user.id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already shared with this user",
        )

    share = SharedResource(
        resource_type=resource_type,
        resource_id=resource_id,
        shared_with_user_id=target_user.id,
        shared_by_user_id=current_user.id,
    )
    db.add(share)
    db.commit()
    return {"id": target_user.id, "email": target_user.email, "display_name": target_user.display_name}


def unshare_resource(
    resource_type: str,
    resource_id: int,
    target_user_id: int,
    current_user: User,
    db: Session,
) -> None:
    """Remove sharing."""
    from fastapi import HTTPException, status

    share = db.query(SharedResource).filter(
        SharedResource.resource_type == resource_type,
        SharedResource.resource_id == resource_id,
        SharedResource.shared_with_user_id == target_user_id,
    ).first()
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found",
        )
    db.delete(share)
    db.commit()


def list_shared_users(resource_type: str, resource_id: int, db: Session) -> list[dict]:
    """List users that this resource is shared with."""
    shares = db.query(SharedResource).filter(
        SharedResource.resource_type == resource_type,
        SharedResource.resource_id == resource_id,
    ).all()

    result = []
    for share in shares:
        user = db.query(User).filter(User.id == share.shared_with_user_id).first()
        if user:
            result.append({"id": user.id, "email": user.email, "display_name": user.display_name})
    return result


def get_shared_resource_ids(resource_type: str, user_id: int, db: Session) -> list[int]:
    """Get IDs of resources shared with this user."""
    rows = db.query(SharedResource.resource_id).filter(
        SharedResource.resource_type == resource_type,
        SharedResource.shared_with_user_id == user_id,
    ).all()
    return [row[0] for row in rows]