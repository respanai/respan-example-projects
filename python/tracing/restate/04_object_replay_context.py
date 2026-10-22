"""Native object registration, replay-attempt context and caller cleanup."""

import asyncio
from contextlib import asynccontextmanager

import restate
from _shared import (
    create_respan,
    example_context,
    finish_respan,
    invoke_registered_handler,
)
from respan import workflow
from restate.server_context import current_context


@workflow(name="restate_object_replay")
async def object_replay(public_input: str):
    lifecycle = []

    @asynccontextmanager
    async def callback():
        lifecycle.append("enter")
        try:
            yield
        finally:
            lifecycle.append("exit")

    obj = restate.VirtualObject(
        "CounterObject",
        invocation_context_managers=[callback],
        metadata={"team": "audit"},
    )

    @obj.handler(name="increment", metadata={"purpose": "counter"})
    async def increment(ctx, value: dict):
        assert current_context() is ctx
        return {"value": value["value"] + 1}

    result = await invoke_registered_handler(
        obj,
        "increment",
        {"value": 41},
        invocation_id="object-replay-1",
        key=public_input,
        replaying=True,
    )
    assert result == {"value": 42} and lifecycle == ["enter", "exit"]
    return result


async def main():
    respan = create_respan()
    try:
        with example_context("object_replay_context"):
            print(await object_replay("counter-42"))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
