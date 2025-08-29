import uvloop
from litestar import Litestar, get, post
from litestar.response import Response

from performance.infra import cache_get, cache_set, db_get_one, db_insert, infra


@get("/ping")
async def ping() -> dict:  # type: ignore[override]
    return {"ok": True}


@get("/db/one")
async def db_one(id: int = 1) -> Response:
    data = await db_get_one(id)
    if not data:
        return Response({"error": "not found"}, status_code=404)
    return Response(data)


@post("/db/insert")
async def db_ins(data: str = "x" * 64) -> dict:
    new_id = await db_insert(data)
    return {"id": new_id}


@get("/cache/get")
async def cget(key: str = "k") -> dict:
    val = await cache_get(key)
    return {"key": key, "value": val}


@get("/cache/set")
async def cset(key: str = "k", value: str = "v") -> dict:
    await cache_set(key, value, 60)
    return {"ok": True}


@get("/mix")
async def mix(id: int = 1) -> dict:
    data = await db_get_one(id)
    cached = await cache_get("mix:" + str(id))
    if cached is None:
        await cache_set("mix:" + str(id), data["payload"] if data else "none", 30)
    return {"db": data, "cached": cached}


async def on_startup() -> None:
    await infra.startup()


async def on_shutdown() -> None:
    await infra.shutdown()


uvloop.install()

app = Litestar(
    route_handlers=[ping, db_one, db_ins, cget, cset, mix],
    on_startup=[on_startup],
    on_shutdown=[on_shutdown],
)
