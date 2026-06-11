from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.sqlalchemy_database_uri, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

redis_client = AsyncRedis.from_url(settings.redis_url, decode_responses=True)
redis_sync_client = SyncRedis.from_url(settings.redis_url, decode_responses=True)
