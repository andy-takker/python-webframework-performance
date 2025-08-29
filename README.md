# Python WebFrameworks Performance

## Run services

```bash
docker compose up --build -d
```

## Test Performance

### Ping

```bash
wrk -t8 -c512 -d2m http://APP_HOST:8001/ping          # aiohttp
wrk -t8 -c512 -d2m http://APP_HOST:8002/ping          # litestar
wrk -t8 -c512 -d2m http://APP_HOST:8003/ping          # fastapi
```

### Read from DB

```bash
wrk -t8 -c512 -d2m --latency -s ./wrk_scripts/db_one.lua http://APP_HOST:8001
wrk -t8 -c512 -d2m --latency -s ./wrk_scripts/db_one.lua http://APP_HOST:8002
wrk -t8 -c512 -d2m --latency -s ./wrk_scripts/db_one.lua http://APP_HOST:8003
```
