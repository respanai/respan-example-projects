"""Use Burr's native async builder, stream container, and final result."""

import asyncio
from collections.abc import AsyncGenerator

from _shared import create_respan, new_run_id, print_trace_lookup
from burr.core import ApplicationBuilder, State
from burr.core.action import streaming_action

EXAMPLE_NAME = "08_async_stream_and_builder"
WORKFLOW_NAME = "Burr Async Stream Workflow"


@streaming_action(reads=["prompt"], writes=["response"])
async def respond(state: State) -> AsyncGenerator[tuple[dict, State | None], None]:
    for chunk in ("async", " stream"):
        await asyncio.sleep(0)
        yield {"delta": chunk}, None
    yield {"response": "async stream"}, state.update(response="async stream")


async def main() -> None:
    run_id = new_run_id(EXAMPLE_NAME)
    runtime = create_respan(
        workflow_name=WORKFLOW_NAME, run_id=run_id, example_name=EXAMPLE_NAME
    )
    app = await (
        ApplicationBuilder()
        .with_actions(respond)
        .with_entrypoint("respond")
        .with_identifiers(
            app_id=f"{run_id}:{EXAMPLE_NAME}", partition_key="controlled-async-thread"
        )
        .with_state(prompt="controlled async prompt")
        .abuild()
    )
    try:
        _, stream = await app.astream_result(halt_after=["respond"])
        chunks = [item["delta"] async for item in stream]
        result, state = await stream.get()
        assert "".join(chunks) == result["response"] == state["response"]
        print_trace_lookup(workflow_name=WORKFLOW_NAME, run_id=run_id)
    finally:
        runtime.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
