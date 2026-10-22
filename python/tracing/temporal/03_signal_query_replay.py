"""Validate real signal/query propagation and replay-safe telemetry."""

import asyncio

from _shared import (
    create_environment,
    create_respan,
    finish_respan,
    marker,
    temporal_id,
)
from _workflows import ApprovalWorkflow
from respan import propagate_attributes
from temporalio.worker import Replayer, Worker


async def main() -> None:
    respan, instrumentor = create_respan("signal-query-replay")
    try:
        async with await create_environment(instrumentor) as environment:
            async with Worker(
                environment.client,
                task_queue="respan-temporal-signal",
                workflows=[ApprovalWorkflow],
            ):
                with propagate_attributes(
                    trace_group_identifier="ApprovalWorkflow",
                    custom_identifier=marker(),
                    metadata={
                        "run_id": marker(),
                        "example_run_id": marker(),
                        "script": "03_signal_query_replay.py",
                    },
                ):
                    handle = await environment.client.start_workflow(
                        ApprovalWorkflow.run,
                        "trace-release",
                        id=temporal_id("signal"),
                        task_queue="respan-temporal-signal",
                    )
                    before = await handle.query(ApprovalWorkflow.status)
                    await handle.signal(ApprovalWorkflow.approve)
                    result = await handle.result()
                    history = await handle.fetch_history()
            await Replayer(
                workflows=[ApprovalWorkflow], interceptors=[instrumentor.interceptor]
            ).replay_workflow(history)
            assert before == "pending"
            assert result == "approved:trace-release"
            print({"before": before, "result": result, "replayed": True})
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
