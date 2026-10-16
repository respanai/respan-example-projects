from _protocol import Protocol
from _shared import run_scenario


def scenario():
    with Protocol() as native, native.client() as client:
        native.count = 75
        native.dim = 5001
        result = client.collections.use("Docs").query.fetch_objects(
            limit=75, include_vector=True
        )
        assert (
            len(result.objects) == 75
            and len(result.objects[0].vector["default"]) == 5001
        )
        assert (
            result.objects[0].properties["flag"] is False
            and result.objects[0].properties["zero"] == 0
        )
        assert str(result.objects[0].uuid) == "00000000-0000-0000-0000-000000000000"
        return {"rows": 75, "dimensions": 5001, "native_type": type(result).__name__}


if __name__ == "__main__":
    run_scenario("full-results", scenario)
