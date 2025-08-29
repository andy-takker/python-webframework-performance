import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import asyncpg
from dishka import BaseScope, Provider, Scope, provide
from dishka.entities.component import Component


@asynccontextmanager
async def create_db_pool(
    db_url: str,
    conn_pool_size: int,
) -> AsyncGenerator[asyncpg.Pool, None]:
    pool = await asyncpg.create_pool(
        dsn=db_url,
        min_size=max(1, conn_pool_size // 4),
        max_size=conn_pool_size,
        timeout=10.0,
    )
    yield pool
    await pool.close()


class Database:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def get_one(self, item_id: int) -> dict | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, payload FROM items WHERE id=$1", item_id
            )
            return dict(row) if row else None

    async def insert(self, payload: str) -> int:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "INSERT INTO items (payload) VALUES ($1) RETURNING id", payload
            )


@dataclass(frozen=True, kw_only=True, slots=True)
class DatabaseConfig:
    url: str = field(default_factory=lambda: os.environ["DATABASE_URL"])
    pool_size: int = field(
        default_factory=lambda: int(os.getenv("DATABASE_POOL_SIZE", "50"))
    )


class DatabaseProvider(Provider):
    def __init__(
        self,
        config: DatabaseConfig,
        scope: BaseScope | None = None,
        component: Component | None = None,
    ):
        super().__init__(scope, component)
        self._config = config

    @provide(scope=Scope.APP)
    async def db_pool(self) -> AsyncGenerator[asyncpg.Pool, None]:
        async with create_db_pool(self._config.url, self._config.pool_size) as pool:
            yield pool

    @provide(scope=Scope.APP)
    async def database(self, db_pool: asyncpg.Pool) -> Database:
        return Database(db_pool)
