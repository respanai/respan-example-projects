"""Released Superagent SDK scenario: content_policy."""

import asyncio
from pathlib import Path

from _shared import client_context, create_respan, example_marker, finish_respan
from respan import propagate_attributes, workflow

SCRIPT_NAME = Path(__file__).name


@workflow(name=SCRIPT_NAME)
async def run_private(scenario: str):
    text = "private fixture-email@example.com"
    import os

    from opentelemetry import context
    from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY

    previous = os.environ.get("TRACELOOP_TRACE_CONTENT")
    try:
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
        with client_context() as client:
            await client.redact(input=text, model="openai/gpt-4o-mini")
    finally:
        if previous is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = previous
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    try:
        with client_context() as client:
            await client.guard(input=text, model="openai/gpt-4o-mini")
    finally:
        context.detach(token)
    token = context.attach(
        context.set_value(context._SUPPRESS_INSTRUMENTATION_KEY, True)
    )
    try:
        with client_context() as client:
            await client.guard(input="suppressed-marker", model="openai/gpt-4o-mini")
    finally:
        context.detach(token)
    return {"private_calls": 2, "suppressed_calls": 1}


async def main():
    respan = create_respan(SCRIPT_NAME)
    marker = example_marker()
    try:
        with propagate_attributes(
            trace_group_identifier=SCRIPT_NAME,
            thread_identifier=marker + "-thread",
            metadata={
                "run_id": marker,
                "integration": "superagent",
                "example": SCRIPT_NAME,
            },
        ):
            result = await run_private("privacy-fixture")
            print(result)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
