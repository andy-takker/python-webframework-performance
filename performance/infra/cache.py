import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from dishka import BaseScope, Provider, Scope, provide
from dishka.entities.component import Component
from redis.asyncio import Redis


@asynccontextmanager
async def create_redis(
    redis_url: str, redis_pool_size: int
) -> AsyncGenerator[Redis, None]:
    redis = Redis.from_url(
        redis_url,
        max_connections=redis_pool_size,
        decode_responses=True,
    )
    yield redis
    await redis.close()


class Cache:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def get(self, key: str) -> str | None:
        return await self.redis.get(key)

    async def set(self, key: str, value: str, ttl: int = 60) -> None:
        await self.redis.set(key, value, ex=ttl)


@dataclass(frozen=True, kw_only=True, slots=True)
class RedisConfig:
    url: str = field(default_factory=lambda: os.environ["REDIS_URL"])
    pool_size: int = field(
        default_factory=lambda: int(os.getenv("REDIS_POOL_SIZE", "100"))
    )


class RedisProvider(Provider):
    def __init__(
        self,
        config: RedisConfig,
        scope: BaseScope | None = None,
        component: Component | None = None,
    ):
        super().__init__(scope, component)
        self._config = config

    @provide(scope=Scope.APP)
    async def redis(self) -> AsyncGenerator[Redis, None]:
        async with create_redis(self._config.url, self._config.pool_size) as redis:
            yield redis

    @provide(scope=Scope.APP)
    async def cache(self, redis: Redis) -> Cache:
        return Cache(redis)
