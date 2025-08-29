import os

import asyncpg
from redis.asyncio import Redis

DB_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ["REDIS_URL"]
CONN_POOL_SIZE = int(os.getenv("CONN_POOL_SIZE", "50"))
REDIS_POOL_SIZE = int(os.getenv("REDIS_POOL_SIZE", "100"))


class Infra:
    def __init__(self) -> None:
        self.db_pool: asyncpg.Pool | None = None
        self.redis: Redis | None = None

    async def startup(self) -> None:
        self.db_pool = await asyncpg.create_pool(
            dsn=DB_URL,
            min_size=max(1, CONN_POOL_SIZE // 4),
            max_size=CONN_POOL_SIZE,
            timeout=10.0,
        )
        self.redis = Redis.from_url(
            REDIS_URL, max_connections=REDIS_POOL_SIZE, decode_responses=True
        )

    async def shutdown(self) -> None:
        if self.redis:
            await self.redis.close()
        if self.db_pool:
            await self.db_pool.close()


infra = Infra()


async def db_get_one(item_id: int) -> dict | None:
    if infra.db_pool is None:
        raise Exception("db_pool is not initialized")
    async with infra.db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, payload FROM items WHERE id=$1", item_id)
        return dict(row) if row else None


async def db_insert(payload: str) -> int:
    if infra.db_pool is None:
        raise Exception("db_pool is not initialized")
    async with infra.db_pool.acquire() as conn:
        return await conn.fetchval(
            "INSERT INTO items (payload) VALUES ($1) RETURNING id", payload
        )


async def cache_get(key: str) -> str | None:
    if infra.redis is None:
        raise Exception("redis is not initialized")
    return await infra.redis.get(key)


async def cache_set(key: str, value: str, ttl: int = 60) -> None:
    if infra.redis is None:
        raise Exception("redis is not initialized")
    await infra.redis.set(key, value, ex=ttl)
