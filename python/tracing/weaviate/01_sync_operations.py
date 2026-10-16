from _protocol import Protocol
from _shared import run_scenario


def scenario():
    with Protocol() as native, native.client() as client:
        col = client.collections.create("Docs")
        identifier = col.data.insert(
            {"text": "native local HTTP", "flag": False, "zero": 0}, vector=[0.25] * 4
        )
        result = col.query.near_vector(
            near_vector=[0.25] * 4, limit=3, include_vector=True
        )
        total = col.aggregate.over_all(total_count=True).total_count
        assert len(result.objects) == total == 3
        client.collections.delete("Docs")
        return {
            "rows": len(result.objects),
            "total": total,
            "native_id": str(identifier),
        }


if __name__ == "__main__":
    run_scenario("sync-operations", scenario)
