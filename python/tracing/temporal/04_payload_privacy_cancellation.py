"""Capture complete payloads and retain native privacy/cancellation behavior."""

from __future__ import annotations

import asyncio
import json

from _shared import (
    create_environment,
    create_respan,
    finish_respan,
    marker,
    temporal_id,
)
from _workflows import ApprovalWorkflow, PayloadWorkflow, echo_payload
from opentelemetry import context
from opentelemetry.semconv_ai import SpanAttributes
from respan import propagate_attributes
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY
from temporalio.client import WorkflowFailureError
from temporalio.exceptions import CancelledError
from temporalio.worker import Worker


async def main() -> None:
    respan, instrumentor = create_respan("payload-privacy-cancellation")
    payload = {
        "history": [
            {"arguments": list(range(75)), "vector": [0.1, 0.2, 0.3]} for _ in range(45)
        ],
        "text": "complete payload " * 2000,
    }
    try:
        async with await create_environment(instrumentor) as environment:
            async with Worker(
                environment.client,
                task_queue="respan-temporal-payload",
                workflows=[PayloadWorkflow, ApprovalWorkflow],
                activities=[echo_payload],
            ):
                with propagate_attributes(
                    metadata={
                        "run_id": marker(),
                        "example_run_id": marker(),
                        "script": "04_payload_privacy_cancellation.py",
                    }
                ):
                    result = await environment.client.execute_workflow(
                        PayloadWorkflow.run,
                        payload,
                        id=temporal_id("payload"),
                        task_queue="respan-temporal-payload",
                    )
                    assert result == payload
                    token = context.attach(
                        context.set_value(ENABLE_CONTENT_TRACING_KEY, False)
                    )
                    try:
                        hidden = await environment.client.execute_workflow(
                            PayloadWorkflow.run,
                            {"private": "private fixture input"},
                            id=temporal_id("privacy"),
                            task_queue="respan-temporal-payload",
                        )
                        assert hidden == {"private": "private fixture input"}
                    finally:
                        context.detach(token)
                    handle = await environment.client.start_workflow(
                        ApprovalWorkflow.run,
                        "controlled-cancel",
                        id=temporal_id("cancel"),
                        task_queue="respan-temporal-payload",
                    )
                    assert await handle.query(ApprovalWorkflow.status) == "pending"
                    await handle.cancel()
                    try:
                        await handle.result()
                    except WorkflowFailureError as exc:
                        assert isinstance(exc.cause, CancelledError)
                    else:
                        raise AssertionError("expected native cancellation")
            spans = respan.exporter.get_finished_spans()
            assert len(spans) == 14
            assert "private fixture input" not in "\n".join(s.to_json() for s in spans)
            actual = [
                s
                for s in spans
                if s.name
                in ("RunActivity:echo_payload", "CompleteWorkflow:PayloadWorkflow")
                and SpanAttributes.TRACELOOP_ENTITY_OUTPUT in s.attributes
            ]
            assert (
                sum(
                    json.loads(s.attributes[SpanAttributes.TRACELOOP_ENTITY_OUTPUT])
                    == payload
                    for s in actual
                )
                == 2
            )
            print({"full_payload": True, "privacy": True, "cancelled": True})
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
