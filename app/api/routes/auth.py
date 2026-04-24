from datetime import timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import GoogleTokenRequest, LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services.session_store import store_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_token_response(user: User) -> TokenResponse:
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        display_name=payload.display_name,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token_response = _build_token_response(user)
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    await store_refresh_token(token_response.refresh_token, user.id, ttl)
    return token_response


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token_response = _build_token_response(user)
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    await store_refresh_token(token_response.refresh_token, user.id, ttl)
    return token_response


@router.get("/google/url")
def google_auth_url() -> dict[str, str]:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Google Auth not configured")

    query = urlencode(
        {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "id_token",
            "scope": "openid email profile",
            "nonce": "setlistclub",
            "prompt": "select_account",
        }
    )
    return {"url": f"https://accounts.google.com/o/oauth2/v2/auth?{query}"}


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(payload: GoogleTokenRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Auth not configured")

    try:
        info = id_token.verify_oauth2_token(payload.id_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid Google token") from exc

    email = info.get("email")
    sub = info.get("sub")
    name = info.get("name") or email
    if not email or not sub:
        raise HTTPException(status_code=400, detail="Invalid Google payload")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, display_name=name, google_sub=sub)
        db.add(user)
    else:
        user.google_sub = sub
        user.display_name = name

    db.commit()
    db.refresh(user)

    token_response = _build_token_response(user)
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    await store_refresh_token(token_response.refresh_token, user.id, ttl)
    return token_response
