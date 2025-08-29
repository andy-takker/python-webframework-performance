# Python WebFrameworks Performance

WebFrameworks for testing:

- [aiohttp](https://docs.aiohttp.org)
- [fastapi](https://fastapi.tiangolo.com)
- [litestar](https://litestar.dev)

## Description

Here 3 identical web applications with the same components and routes are described:

Components:

- Database - [asyncpg](https://github.com/MagicStack/asyncpg);
- Cache - [redis](https://github.com/redis/redis-py);
- DI - [dishka](https://dishka.readthedocs.io/en/stable/);

Routes:

- `GET /ping`
- `GET /db/one`
- `POST /db/insert`
- `GET /cache/get`
- `POST /cache/set`
- `GET /mix`

## Run services

```bash
docker compose up --build -d
```

## Test Performance

```bash
export $APP_HOST=127.0.0.1 # or your real IP
```

### Ping

```bash
wrk -t8 -c512 -d2m http://$APP_HOST:8001/ping          # aiohttp
wrk -t8 -c512 -d2m http://$APP_HOST:8002/ping          # litestar
wrk -t8 -c512 -d2m http://$APP_HOST:8003/ping          # fastapi
```

### Read from DB

```bash
wrk -t8 -c512 -d2m --latency -s ./wrk_scripts/db_one.lua http://$APP_HOST:8001
wrk -t8 -c512 -d2m --latency -s ./wrk_scripts/db_one.lua http://$APP_HOST:8002
wrk -t8 -c512 -d2m --latency -s ./wrk_scripts/db_one.lua http://$APP_HOST:8003
```

### Mix

```bash
wrk -t8 -c512 -d2m --latency -s ./wrk_scripts/mix.lua http://$APP_HOST:8001
wrk -t8 -c512 -d2m --latency -s ./wrk_scripts/mix.lua http://$APP_HOST:8002
wrk -t8 -c512 -d2m --latency -s ./wrk_scripts/mix.lua http://$APP_HOST:8003
```

## Experiments

You can try `granian` for litestar and fastapi servers:

```bash
granian performance.server_litestar:app --host 0.0.0.0 --port 8000 --workers 4 --workers-max-rss 1024 --workers-lifetime 6h --interface asginl --loop uvloop --backlog 4096 --backpressure 1024 --no-access-log --log-level info
```

```bash
granian performance.server_litestar:app --interface asginl --workers 4 --workers-lifetime 6h --workers-max-rss 1024 --loop uvloop --backlog 4096 --backpressure 1024 --no-access-log --log-level info
```
