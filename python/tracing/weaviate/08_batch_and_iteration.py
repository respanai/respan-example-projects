from _protocol import Protocol
from _shared import run_scenario


def scenario():
    with Protocol() as native, native.client() as client:
        col = client.collections.use("Docs")
        supplied = 0

        def objects():
            nonlocal supplied
            for i in range(75):
                supplied += 1
                yield {"text": f"native {i}", "flag": False, "zero": 0}

        batch = col.data.ingest(objects())
        result = list(col.iterator(include_vector=True))
        assert supplied == 75 and len(batch.uuids) == 75 and len(result) == 3
        return {
            "ingested": len(batch.uuids),
            "iterated": len(result),
            "native_iterator": type(col.iterator()).__name__,
        }


if __name__ == "__main__":
    run_scenario("batch-and-iteration", scenario)
