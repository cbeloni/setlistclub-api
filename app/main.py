from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, redis_client
from app.models import ChordSheet, Setlist, SetlistItem, User  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Auto-create schema on first boot for the configured MySQL user.
    Base.metadata.create_all(bind=engine)
    await redis_client.ping()
    yield
    await redis_client.aclose()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
