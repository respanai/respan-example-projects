import psycopg
from _shared import run_scenario


def scenario(dsn):
    with psycopg.connect(dsn, autocommit=True) as connection:
        try:
            connection.execute("SELECT * FROM controlled_missing_relation")
        except psycopg.errors.UndefinedTable as error:
            assert error.sqlstate == "42P01"
        else:
            raise AssertionError("native UndefinedTable expected")
        cursor = connection.execute("SELECT id FROM items WHERE false")
        assert cursor.fetchall() == [] and cursor.fetchone() is None
        cursor.close()
        cursor = connection.execute(
            psycopg.sql.SQL("SELECT {},{},{}").format(
                psycopg.sql.Literal(False),
                psycopg.sql.Literal(0),
                psycopg.sql.Literal(""),
            )
        )
        assert cursor.fetchone() == (False, 0, "")
        cursor.close()
    return {
        "native_error": "UndefinedTable",
        "actual_sqlstate": "42P01",
        "empty_rows": 0,
        "null_fetch": True,
        "false_zero_empty_preserved": True,
    }


if __name__ == "__main__":
    run_scenario("06_native_errors_and_empty", scenario)
