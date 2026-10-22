"""Opaque serde remains a single native callback; private request is omitted."""

import asyncio
import json

import restate
from _shared import (
    create_respan,
    example_context,
    finish_respan,
    invoke_registered_handler,
)
from respan import workflow


@workflow(name="restate_custom_serde_privacy")
async def custom_serde(public_input: str):
    class CountingSerde(restate.serde.Serde):
        calls = 0

        def serialize(self, value):
            return json.dumps(value).encode()

        def deserialize(self, value):
            self.calls += 1
            return json.loads(value)

    serde = CountingSerde()
    service = restate.Service("PrivateSerdeService")

    @service.handler(name="process", input_serde=serde)
    async def process(ctx, value):
        return {"accepted": True}

    result = await invoke_registered_handler(
        service,
        "process",
        {"private": "request-body"},
        invocation_id="custom-private-1",
    )
    assert serde.calls == 1 and result == {"accepted": True}
    return {"accepted": True, "serde_calls": serde.calls}


async def main():
    respan = create_respan(capture_content=False)
    try:
        with example_context("custom_serde_privacy"):
            print(await custom_serde("public"))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
