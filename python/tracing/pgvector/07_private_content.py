import pgvector.psycopg as native
import psycopg
from _shared import run_scenario, vector_values
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def scenario(dsn):
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    try:
        with psycopg.connect(dsn, autocommit=True) as connection:
            native.register_vector(connection)
            cursor = connection.execute("SELECT embedding FROM items LIMIT 1")
            row = cursor.fetchone()
            assert len(vector_values(row[0])) == 5001
            cursor.close()
    finally:
        context.detach(token)
    return {"native_dimensions": 5001, "canonical_content_captured": False}


if __name__ == "__main__":
    run_scenario("07_private_content", scenario)
