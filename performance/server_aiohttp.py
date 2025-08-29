import argparse
import logging

import uvloop
from aiohttp import web
from aiomisc import entrypoint
from aiomisc.service.aiohttp import AIOHTTPService
from aiomisc_log import LogFormat, basic_config

from performance.infra import cache_get, cache_set, db_get_one, db_insert, infra


async def handle_ping(request: web.Request) -> web.Response:
    return web.json_response({"ok": True})


async def handle_db_one(request: web.Request) -> web.Response:
    try:
        item_id = int(request.query.get("id", "1"))
    except ValueError:
        return web.json_response({"error": "bad id"}, status=400)
    data = await db_get_one(item_id)
    if not data:
        return web.json_response({"error": "not found"}, status=404)
    return web.json_response(data)


async def handle_db_insert(request: web.Request) -> web.Response:
    payload = (await request.text()) or "x" * 64
    new_id = await db_insert(payload)
    return web.json_response({"id": new_id})


async def handle_cache_get(request: web.Request) -> web.Response:
    key = request.query.get("key", "k")
    val = await cache_get(key)
    return web.json_response({"key": key, "value": val})


async def handle_cache_set(request: web.Request) -> web.Response:
    key = request.query.get("key", "k")
    value = request.query.get("value", "v")
    await cache_set(key, value, 60)
    return web.json_response({"ok": True})


async def handle_mix(request: web.Request) -> web.Response:
    item_id = int(request.query.get("id", "1"))
    # 1×db read + 1×cache get + 1×cache set
    data = await db_get_one(item_id)
    cached = await cache_get("mix:" + str(item_id))
    if cached is None:
        await cache_set("mix:" + str(item_id), data["payload"] if data else "none", 30)
    return web.json_response({"db": data, "cached": cached})


async def on_startup(app: web.Application) -> None:
    await infra.startup()


async def on_cleanup(app: web.Application) -> None:
    await infra.shutdown()


class REST(AIOHTTPService):
    async def create_application(self) -> web.Application:
        app = web.Application()
        app.add_routes(
            [
                web.get("/ping", handle_ping),
                web.get("/db/one", handle_db_one),
                web.post("/db/insert", handle_db_insert),
                web.get("/cache/get", handle_cache_get),
                web.get("/cache/set", handle_cache_set),
                web.get("/mix", handle_mix),
            ]
        )
        app.on_startup.append(on_startup)
        app.on_cleanup.append(on_cleanup)
        return app


def main() -> None:
    uvloop.install()
    parser = argparse.ArgumentParser(description="aiohttp server example")
    parser.add_argument("--path", default="0.0.0.0")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    basic_config(level=logging.INFO, log_format=LogFormat.plain)

    service = REST(address=args.path, port=args.port)
    with entrypoint(service) as loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
