from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvloop
from dishka import FromDishka, make_async_container
from dishka.integrations.litestar import inject, setup_dishka
from litestar import Litestar, get, post
from litestar.response import Response

from performance.infra.cache import Cache, RedisConfig, RedisProvider
from performance.infra.database import Database, DatabaseConfig, DatabaseProvider


@get("/ping")
async def ping() -> dict:  # type: ignore[override]
    return {"ok": True}


@get("/db/one")
@inject
async def db_one(
    db: FromDishka[Database],
    id: int = 1,
) -> Response:
    data = await db.get_one(id)
    if not data:
        return Response({"error": "not found"}, status_code=404)
    return Response(data)


@post("/db/insert")
@inject
async def db_ins(db: FromDishka[Database], data: str = "x" * 64) -> dict:
    new_id = await db.insert(data)
    return {"id": new_id}


@get("/cache/get")
@inject
async def cget(cache: FromDishka[Cache], key: str = "k") -> dict:
    val = await cache.get(key)
    return {"key": key, "value": val}


@get("/cache/set")
@inject
async def cset(cache: FromDishka[Cache], key: str = "k", value: str = "v") -> dict:
    await cache.set(key, value, 60)
    return {"ok": True}


@get("/mix")
@inject
async def mix(
    database: FromDishka[Database],
    cache: FromDishka[Cache],
    id: int = 1,
) -> dict:
    cached_data = await cache.get("mix:" + str(id))
    if cached_data is None:
        data = await database.get_one(id)
        cached_data = data["payload"] if data else "none"
        await cache.set("mix:" + str(id), cached_data, 30)
    return {"data": cached_data}


def create_app() -> Litestar:
    uvloop.install()

    database_config = DatabaseConfig()
    redis_config = RedisConfig()
    container = make_async_container(
        DatabaseProvider(config=database_config),
        RedisProvider(config=redis_config),
    )

    @asynccontextmanager
    async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
        yield
        await container.close()

    app = Litestar(
        lifespan=[lifespan],
        route_handlers=[ping, db_one, db_ins, cget, cset, mix],
    )
    setup_dishka(container, app)
    return app


app = create_app()
