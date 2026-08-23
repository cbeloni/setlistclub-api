from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.migrations import run_migrations
from app.db.session import engine, redis_client
from app.models import ChordSheet, Setlist, SetlistItem, User  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Base schema first, then versioned migrations.
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)

    await redis_client.ping()

    if settings.bucket_configured:
        logger.info(
            "Bucket configurado: endpoint=%s base_url=%s",
            settings.bucket_endpoint,
            settings.bucket_base_url,
        )
    else:
        logger.warning(
            "Bucket NÃO configurado (BUCKET_URL/BUCKET_ACCESS_KEY_ID/BUCKET_SECRET_ACCESS_KEY ausentes ou vazios). "
            "Cifras com imagem/PDF serão gravadas como data URI no banco (legado)."
        )

    yield
    await redis_client.aclose()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://setlistclub.beloni.dev.br",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
