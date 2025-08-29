import argparse
import logging

import uvloop
from aiohttp import web
from aiomisc import entrypoint
from aiomisc.service.aiohttp import AIOHTTPService
from aiomisc_log import LogFormat, basic_config
from dishka import FromDishka, make_async_container
from dishka.integrations.aiohttp import inject, setup_dishka

from performance.infra.cache import Cache, RedisConfig, RedisProvider
from performance.infra.database import Database, DatabaseConfig, DatabaseProvider


async def handle_ping(request: web.Request) -> web.Response:
    return web.json_response({"ok": True})


@inject
async def handle_db_one(
    request: web.Request,
    database: FromDishka[Database],
) -> web.Response:
    try:
        item_id = int(request.query.get("id", "1"))
    except ValueError:
        return web.json_response({"error": "bad id"}, status=400)
    data = await database.get_one(item_id)
    if not data:
        return web.json_response({"error": "not found"}, status=404)
    return web.json_response(data)


@inject
async def handle_db_insert(
    request: web.Request,
    database: FromDishka[Database],
) -> web.Response:
    payload = (await request.text()) or "x" * 64
    new_id = await database.insert(payload)
    return web.json_response({"id": new_id})


@inject
async def handle_cache_get(
    request: web.Request,
    cache: FromDishka[Cache],
) -> web.Response:
    key = request.query.get("key", "k")
    val = await cache.get(key)
    return web.json_response({"key": key, "value": val})


@inject
async def handle_cache_set(
    request: web.Request,
    cache: FromDishka[Cache],
) -> web.Response:
    key = request.query.get("key", "k")
    value = request.query.get("value", "v")
    await cache.set(key, value, 60)
    return web.json_response({"ok": True})


@inject
async def handle_mix(
    request: web.Request,
    database: FromDishka[Database],
    cache: FromDishka[Cache],
) -> web.Response:
    item_id = int(request.query.get("id", "1"))
    cached_data = await cache.get("mix:" + str(item_id))
    if cached_data is None:
        data = await database.get_one(item_id)
        cached_data = data["payload"] if data else "none"
        await cache.set("mix:" + str(item_id), cached_data, 30)
    return web.json_response({"data": cached_data})


class REST(AIOHTTPService):
    async def create_application(self) -> web.Application:
        database_config = DatabaseConfig()
        redis_config = RedisConfig()
        container = make_async_container(
            DatabaseProvider(config=database_config),
            RedisProvider(config=redis_config),
        )

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
        setup_dishka(container, app)
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
