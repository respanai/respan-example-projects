from _protocol import Protocol
from _shared import run_scenario


async def scenario():
    with Protocol() as native:
        async with native.async_client() as client:
            col = await client.collections.create("Docs")
            identifier = await col.data.insert(
                {"text": "native async HTTP", "flag": False, "zero": 0}
            )
            result = await col.query.hybrid(
                query="native", vector=[0.25] * 4, include_vector=True
            )
            aggregate = await col.aggregate.over_all(total_count=True)
            assert len(result.objects) == aggregate.total_count == 3
            await client.collections.delete("Docs")
            return {"rows": len(result.objects), "native_id": str(identifier)}


if __name__ == "__main__":
    run_scenario("async-operations", scenario)
