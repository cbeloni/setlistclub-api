from app.db.session import redis_client


async def store_refresh_token(token: str, user_id: int, ttl_seconds: int) -> None:
    await redis_client.setex(f"refresh:{token}", ttl_seconds, str(user_id))


async def revoke_refresh_token(token: str) -> None:
    await redis_client.delete(f"refresh:{token}")
