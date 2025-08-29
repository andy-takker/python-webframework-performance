# file: db_init.py
import asyncio
import os
import random
import string

import asyncpg

DB_URL = os.getenv("DATABASE_URL")

DDL = """
CREATE TABLE IF NOT EXISTS items (
  id BIGSERIAL PRIMARY KEY,
  payload TEXT NOT NULL
);
"""


async def main() -> None:
    conn = await asyncpg.connect(DB_URL)
    try:
        await conn.execute(DDL)
        # наполним таблицу ~100k строк для реалистичных чтений
        count = await conn.fetchval("SELECT count(*) FROM items;")
        if count < 100_000:
            payload = "".join(
                random.choices(string.ascii_letters + string.digits, k=120)
            )
            # батчами для скорости
            for _ in range((100_000 - count) // 1000):
                await conn.executemany(
                    "INSERT INTO items (payload) VALUES ($1)", [(payload,)] * 1000
                )
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
