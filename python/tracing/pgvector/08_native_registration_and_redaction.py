import pgvector.psycopg2 as pg2
import psycopg
import psycopg2
from _shared import run_scenario


def scenario(dsn):
    connection = psycopg2.connect(dsn)
    try:
        assert pg2.register_vector(connection) is None
    finally:
        connection.close()
    value = {
        "properties": {
            "api_key": {"type": "string", "example": "controlled-schema-secret"}
        },
        "quoted": 'Bearer "controlled quoted secret"',
        "url": "https://example.invalid/path?api%5Fkey=controlled-url-secret",
        "flag": False,
        "zero": 0,
        "empty": "",
    }
    with psycopg.connect(dsn, autocommit=True) as connection:
        cursor = connection.execute(
            "SELECT %(password)s::text AS password,%(payload)s::jsonb AS payload",
            {
                "password": "controlled-column-secret",
                "payload": psycopg.types.json.Jsonb(value),
            },
        )
        row = cursor.fetchone()
        assert row == ("controlled-column-secret", value)
        cursor.close()
    return {
        "native_psycopg2_registration": True,
        "native_tuple_values_preserved": True,
        "schema_property_retained": True,
    }


if __name__ == "__main__":
    run_scenario("08_native_registration_and_redaction", scenario)
