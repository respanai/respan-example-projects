"""Trace an asynchronous Burr application execution."""

import asyncio

from _shared import create_respan, new_run_id, print_trace_lookup, workflow_context
from burr.core import ApplicationBuilder, State, action

WORKFLOW_NAME = "Burr Async Workflow"
EXAMPLE_NAME = "05_async_workflow"


@action(reads=["value"], writes=["value"])
async def double_value(state: State) -> State:
    await asyncio.sleep(0)
    return state.update(value=state["value"] * 2)


async def main() -> None:
    run_id = new_run_id(EXAMPLE_NAME)
    respan = create_respan(
        workflow_name=WORKFLOW_NAME,
        run_id=run_id,
        example_name=EXAMPLE_NAME,
    )
    app = (
        ApplicationBuilder()
        .with_identifiers(app_id=f"{run_id}:{EXAMPLE_NAME}", partition_key="user-async")
        .with_actions(double_value)
        .with_entrypoint("double_value")
        .with_state(value=21)
        .build()
    )
    try:
        with workflow_context(
            respan,
            workflow_name=WORKFLOW_NAME,
            run_id=run_id,
            example_name=EXAMPLE_NAME,
        ):
            _, _, state = await app.arun(halt_after=["double_value"])
        assert state["value"] == 42
        print(f"Async value: {state['value']}")
        print_trace_lookup(workflow_name=WORKFLOW_NAME, run_id=run_id)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
