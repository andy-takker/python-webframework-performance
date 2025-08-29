from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvloop
from dishka import FromDishka, make_async_container
from dishka.integrations.fastapi import DishkaRoute, setup_dishka
from fastapi import APIRouter, Body, FastAPI, HTTPException, Query
from pydantic import BaseModel

from performance.infra.cache import Cache, RedisConfig, RedisProvider
from performance.infra.database import Database, DatabaseConfig, DatabaseProvider


class InsertPayload(BaseModel):
    data: str | None = None


router = APIRouter(route_class=DishkaRoute)


@router.get("/ping")
async def ping() -> dict:
    return {"ok": True}


@router.get("/db/one")
async def db_one(database: FromDishka[Database], id: int = Query(1, ge=1)) -> dict:
    data = await database.get_one(id)
    if not data:
        raise HTTPException(status_code=404, detail="not found")
    return data


@router.post("/db/insert")
async def db_ins(
    database: FromDishka[Database],
    data_q: str | None = Query(None),
    payload: InsertPayload = Body(default=InsertPayload()),
) -> dict:
    data = data_q if data_q is not None else payload.data
    if data is None:
        data = "x" * 64
    new_id = await database.insert(data)
    return {"id": new_id}


@router.get("/cache/get")
async def cache_get_route(
    cache: FromDishka[Cache],
    key: str = Query("k"),
) -> dict:
    val = await cache.get(key)
    return {"key": key, "value": val}


@router.get("/cache/set")
async def cache_set_route(
    cache: FromDishka[Cache],
    key: str = Query("k"),
    value: str = Query("v"),
    ttl: int = Query(60, ge=1),
) -> dict:
    await cache.set(key, value, ttl)
    return {"ok": True}


@router.get("/mix")
async def mix(
    database: FromDishka[Database],
    cache: FromDishka[Cache],
    id: int = Query(1, ge=1),
) -> dict:
    cached_data = await cache.get("mix:" + str(id))
    if cached_data is None:
        data = await database.get_one(id)
        cached_data = data["payload"] if data else "none"
        await cache.set("mix:" + str(id), cached_data, 30)
    return {"data": cached_data}


def create_app() -> FastAPI:
    uvloop.install()

    database_config = DatabaseConfig()
    redis_config = RedisConfig()
    container = make_async_container(
        DatabaseProvider(config=database_config),
        RedisProvider(config=redis_config),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield
        await container.close()

    app = FastAPI(title="FastAPI Benchmark App", lifespan=lifespan)
    app.include_router(router)
    setup_dishka(container, app)
    return app


app = create_app()
