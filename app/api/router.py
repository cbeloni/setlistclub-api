from fastapi import APIRouter

from app.api.routes import auth, chord_sheets, setlists

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(chord_sheets.router)
api_router.include_router(setlists.router)
