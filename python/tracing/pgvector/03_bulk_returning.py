import psycopg
from _shared import run_scenario


def scenario(dsn):
    seen = []

    def rows():
        for i in range(75):
            seen.append(i)
            yield (1000 + i,)

    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            assert (
                cursor.executemany("INSERT INTO items(id) VALUES (%s)", rows()) is None
            )
            assert cursor.rowcount == 75 and seen == list(range(75))
            assert (
                cursor.executemany(
                    "INSERT INTO items(id) VALUES (%s) RETURNING id",
                    [(2000,), (2001,)],
                    returning=True,
                )
                is None
            )
            first = cursor.fetchone()
            assert cursor.nextset() is True
            second = cursor.fetchone()
            assert (first, second) == ((2000,), (2001,))
        connection.rollback()
        return {
            "native_bulk_rows": 75,
            "native_generator_consumptions": len(seen),
            "native_returning_sets": 2,
            "transaction": "rolled back",
        }


if __name__ == "__main__":
    run_scenario("03_bulk_returning", scenario)
