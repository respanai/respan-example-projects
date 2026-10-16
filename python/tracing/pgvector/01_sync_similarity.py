import pgvector.psycopg as native
import psycopg
from _shared import Vector, run_scenario, vector_values


def scenario(dsn):
    with psycopg.connect(dsn, autocommit=True) as connection:
        assert native.register_vector(connection) is None
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id,embedding,payload,flag,zero,empty,embedding <-> %s AS distance FROM items ORDER BY id",
                (Vector([0.0] * 5001),),
            )
            rows = cursor.fetchall()
            assert len(rows) == 75 and all(
                len(vector_values(row[1])) == 5001 for row in rows
            )
            assert rows[0][3:] == (False, 0, "", 0.0)
            assert len(rows[0][2]["history"]) == 75
        return {
            "native_rows": 75,
            "vector_dimensions": 5001,
            "history_items": 75,
            "actual_distance": rows[0][-1],
        }


if __name__ == "__main__":
    run_scenario("01_sync_similarity", scenario)
