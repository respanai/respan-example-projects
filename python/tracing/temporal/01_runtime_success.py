"""Run a real local Temporal workflow and activity success path."""

import asyncio

from _shared import (
    create_environment,
    create_respan,
    finish_respan,
    marker,
    temporal_id,
)
from _workflows import GreetingWorkflow, compose_greeting
from respan import propagate_attributes
from temporalio.worker import Worker


async def main() -> None:
    respan, instrumentor = create_respan("runtime-success")
    try:
        async with (
            await create_environment(instrumentor) as environment,
            Worker(
                environment.client,
                task_queue="respan-temporal-success",
                workflows=[GreetingWorkflow],
                activities=[compose_greeting],
            ),
        ):
            with propagate_attributes(
                trace_group_identifier="GreetingWorkflow",
                custom_identifier=marker(),
                metadata={
                    "run_id": marker(),
                    "example_run_id": marker(),
                    "script": "01_runtime_success.py",
                },
            ):
                result = await environment.client.execute_workflow(
                    GreetingWorkflow.run,
                    "Ada",
                    id=temporal_id("success"),
                    task_queue="respan-temporal-success",
                )
            assert result == "Hello, Ada!"
            print({"result": result})
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
