import pgvector.psycopg as native
import psycopg
from _shared import Vector, run_scenario, vector_values


async def scenario(dsn):
    async with await psycopg.AsyncConnection.connect(
        dsn, autocommit=True
    ) as connection:
        await native.register_vector_async(connection)
        async with connection.cursor() as cursor:
            await cursor.execute(
                "SELECT id,embedding,embedding <=> %s AS distance FROM items WHERE id<3 ORDER BY id",
                (Vector([0.25] * 5001),),
            )
            rows = await cursor.fetchall()
            assert len(rows) == 3 and len(vector_values(rows[0][1])) == 5001
        cursor = await connection.execute("SELECT false,0,''::text")
        row = await cursor.fetchone()
        assert row == (False, 0, "")
        await cursor.close()
        return {
            "native_rows": 3,
            "vector_dimensions": 5001,
            "native_cursor_type": type(cursor).__name__,
        }


if __name__ == "__main__":
    run_scenario("02_async_similarity", scenario)
