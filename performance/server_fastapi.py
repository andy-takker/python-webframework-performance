from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvloop
from fastapi import Body, FastAPI, HTTPException, Query
from pydantic import BaseModel

from performance.infra import cache_get, cache_set, db_get_one, db_insert, infra


class InsertPayload(BaseModel):
    data: str | None = None


uvloop.install()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await infra.startup()
    yield
    await infra.shutdown()


app = FastAPI(title="FastAPI Benchmark App", lifespan=lifespan)


@app.get("/ping")
async def ping() -> dict:
    return {"ok": True}


@app.get("/db/one")
async def db_one(id: int = Query(1, ge=1)) -> dict:
    data = await db_get_one(id)
    if not data:
        raise HTTPException(status_code=404, detail="not found")
    return data


@app.post("/db/insert")
async def db_ins(
    data_q: str | None = Query(None),
    payload: InsertPayload = Body(default=InsertPayload()),
) -> dict:
    data = data_q if data_q is not None else payload.data
    if data is None:
        data = "x" * 64
    new_id = await db_insert(data)
    return {"id": new_id}


@app.get("/cache/get")
async def cache_get_route(key: str = Query("k")) -> dict:
    val = await cache_get(key)
    return {"key": key, "value": val}


@app.get("/cache/set")
async def cache_set_route(
    key: str = Query("k"),
    value: str = Query("v"),
    ttl: int = Query(60, ge=1),
) -> dict:
    await cache_set(key, value, ttl)
    return {"ok": True}


@app.get("/mix")
async def mix(id: int = Query(1, ge=1)) -> dict:
    data = await db_get_one(id)
    cached = await cache_get("mix:" + str(id))
    if cached is None:
        await cache_set("mix:" + str(id), data["payload"] if data else "none", 30)
    return {"db": data, "cached": cached}
