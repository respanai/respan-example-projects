import pgvector.psycopg as native
import psycopg
from _shared import Bit, HalfVector, SparseVector, Vector, run_scenario, vector_values


def scenario(dsn):
    supported = []
    skipped = []
    with psycopg.connect(dsn, autocommit=True) as connection:
        native.register_vector(connection)
        for name, value in [
            ("vector", Vector([0.25] * 5001)),
            ("halfvec", HalfVector([0.25] * 5001)),
            ("sparsevec", SparseVector({0: 1.0, 5000: 2.0}, 5001)),
            ("bit", Bit("1" + "0" * 5000)),
        ]:
            if (
                connection.execute("SELECT to_regtype(%s)", (name,)).fetchone()[0]
                is None
            ):
                skipped.append(name)
                continue
            with connection.cursor() as cursor:
                typ = name if name != "bit" else "bit(5001)"
                cursor.execute(f"SELECT %s::{typ}", (value,))
                row = cursor.fetchone()
                if name in ("vector", "halfvec"):
                    assert len(vector_values(row[0])) == 5001
                elif name == "sparsevec":
                    assert row[0].dimensions() == 5001 and row[0].indices() == [0, 5000]
                else:
                    assert len(row[0]) == 5001
            supported.append(name)
    return {
        "native_types": supported,
        "native_extension_capability_skips": skipped,
        "dimensions": 5001,
    }


if __name__ == "__main__":
    run_scenario("05_native_vector_types", scenario)
