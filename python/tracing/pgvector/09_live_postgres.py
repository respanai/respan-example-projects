"""Optional existing PostgreSQL server; never creates an external database."""

import os

import pgvector.psycopg as native
import psycopg
from _shared import _run_scenario


def scenario(dsn):
    with psycopg.connect(dsn, autocommit=True) as connection:
        native.register_vector(connection)
        cursor = connection.execute("SELECT 1")
        assert cursor.fetchone() == (1,)
        cursor.close()
        return {"native_registered": True, "native_query_success": True}


if __name__ == "__main__":
    if os.getenv("RESPAN_PGVECTOR_LIVE") != "1":
        print("SKIP existing PostgreSQL: set RESPAN_PGVECTOR_LIVE=1 and PGVECTOR_DSN")
    else:
        _run_scenario("09_live_postgres", scenario, os.environ["PGVECTOR_DSN"])
