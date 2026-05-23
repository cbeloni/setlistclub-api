from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, redis_client
from app.models import ChordSheet, Setlist, SetlistItem, User  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Auto-create schema on first boot for the configured MySQL user.
    Base.metadata.create_all(bind=engine)

    # Auto-create test user if not present
    from app.db.session import SessionLocal
    from app.models.user import User
    from app.core.security import get_password_hash

    db = SessionLocal()
    try:
        test_user = db.query(User).filter(User.email == "teste@teste.com").first()
        if not test_user:
            test_user = User(
                email="teste@teste.com",
                display_name="Usuário de Teste",
                hashed_password=get_password_hash("123"),
            )
            db.add(test_user)
            db.commit()
    except Exception as e:
        print(f"Error seeding test user: {e}")
    finally:
        db.close()

    await redis_client.ping()
    yield
    await redis_client.aclose()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://setlistclub.beloni.dev.br",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
