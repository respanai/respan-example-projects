import asyncio

from _native import Native
from _shared import Runtime


async def main():
    r = Runtime("async")
    n = Native("controlled async result")
    try:
        with r.workflow():
            assert (
                await n.client.async_run(
                    "owner/model", input={"prompt": "Async generation"}
                )
                == n.output
            )
            stream = await n.client.async_stream(
                "owner/model", input={"prompt": "Async events"}
            )
            assert len([event async for event in stream]) == 251
            prediction = await n.client.predictions.async_create(
                model="owner/model", input={"prompt": "Prediction events"}, stream=True
            )
            events = prediction.async_stream()
            assert (await anext(events)).data == "chunk-0"
            await events.aclose()
            assert await prediction.async_reload() is None
            assert await prediction.async_wait() is None
            assert await prediction.async_cancel() is None
            page = await n.client.predictions.async_list()
            assert page.results[0].id == "controlled"
            await n.client.predictions.async_get("controlled")
            await n.client.predictions.async_cancel("controlled")
            await n.client.models.predictions.async_create(
                model="owner/model", input={"prompt": "Model route"}
            )
            await n.client.deployments.predictions.async_create(
                deployment="owner/deployment", input={"prompt": "Deployment route"}
            )
    finally:
        await n.client._async_client.aclose()
        n.close()
        r.close()


asyncio.run(main())
