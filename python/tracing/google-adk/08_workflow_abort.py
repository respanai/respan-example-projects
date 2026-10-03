"""ADK2.11 abort_signal closes an in-flight workflow node."""

import asyncio

from _shared import APP_USER_ID, make_runner, make_user_message, run_scenario
from google.adk.workflow import START, Workflow, node


async def scenario():
    started, abort = asyncio.Event(), asyncio.Event()

    @node
    async def waiting(node_input: str):
        started.set()
        await asyncio.Event().wait()
        return "unreachable"

    runner, session = await make_runner(
        node=Workflow(name="abort_workflow", edges=[(START, waiting)])
    )

    async def consume():
        return [
            event
            async for event in runner.run_async(
                user_id=APP_USER_ID,
                session_id=session.id,
                new_message=make_user_message("Synthetic abort request"),
                abort_signal=abort,
            )
        ]

    task = asyncio.create_task(consume())
    await asyncio.wait_for(started.wait(), 3)
    abort.set()
    await asyncio.wait_for(task, 3)
    return {"aborted": True}


if __name__ == "__main__":
    run_scenario("08_workflow_abort", scenario)
