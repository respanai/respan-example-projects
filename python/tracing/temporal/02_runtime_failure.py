"""Run a real local Temporal activity/workflow failure path."""

import asyncio

from _shared import (
    create_environment,
    create_respan,
    finish_respan,
    marker,
    temporal_id,
)
from _workflows import FailingWorkflow, fail_once
from respan import propagate_attributes
from temporalio.client import WorkflowFailureError
from temporalio.worker import Worker


async def main() -> None:
    respan, instrumentor = create_respan("runtime-failure")
    try:
        async with (
            await create_environment(instrumentor) as environment,
            Worker(
                environment.client,
                task_queue="respan-temporal-failure",
                workflows=[FailingWorkflow],
                activities=[fail_once],
            ),
        ):
            try:
                with propagate_attributes(
                    trace_group_identifier="FailingWorkflow",
                    custom_identifier=marker(),
                    metadata={
                        "run_id": marker(),
                        "example_run_id": marker(),
                        "script": "02_runtime_failure.py",
                    },
                ):
                    await environment.client.execute_workflow(
                        FailingWorkflow.run,
                        "expected activity failure",
                        id=temporal_id("failure"),
                        task_queue="respan-temporal-failure",
                    )
            except WorkflowFailureError as exc:
                print({"expected_error": type(exc.cause).__name__})
            else:
                raise AssertionError("expected Temporal workflow failure did not occur")
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
