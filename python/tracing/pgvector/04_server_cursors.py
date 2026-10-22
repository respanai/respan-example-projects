import psycopg
from _shared import run_scenario


async def async_part(dsn):
    async with await psycopg.AsyncConnection.connect(dsn) as connection:
        async with connection.cursor(name="controlled_async_portal") as cursor:
            await cursor.execute("SELECT id FROM items ORDER BY id")
            first = await cursor.fetchmany(2)
            rest = await cursor.fetchall()
            assert (
                type(cursor) is psycopg.AsyncServerCursor
                and len(first) + len(rest) == 75
            )
        assert cursor.closed
        return {"async_rows": 75, "async_cursor_closed": cursor.closed}


async def scenario(dsn):
    with psycopg.connect(dsn) as connection:
        with connection.cursor(name="controlled_sync_portal") as cursor:
            cursor.execute("SELECT id FROM items ORDER BY id")
            first = cursor.fetchmany(2)
            rest = cursor.fetchall()
            assert type(cursor) is psycopg.ServerCursor and len(first) + len(rest) == 75
        assert cursor.closed
    result = await async_part(dsn)
    result.update(sync_rows=75, sync_cursor_closed=True)
    return result


if __name__ == "__main__":
    run_scenario("04_server_cursors", scenario)
