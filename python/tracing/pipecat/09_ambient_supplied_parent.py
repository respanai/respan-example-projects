"""Ambient opt-out bounds a supplied-context parent and later native children."""

import asyncio

from _pipeline import run
from _shared import attributes, create_respan, finish_respan, marker, print_result
from opentelemetry import context, trace
from opentelemetry.semconv_ai import SpanAttributes as TL
from respan import workflow
from respan_sdk.constants.llm_logging import LOG_TYPE_TASK, LogMethodChoices
from respan_sdk.constants.span_attributes import RESPAN_LOG_METHOD, RESPAN_LOG_TYPE
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


async def main():
    run_id = marker()
    sdk = create_respan("ambient-supplied-parent", run_id)

    @workflow(name="pipecat_ambient_supplied_parent")
    async def scenario():
        private = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        try:
            supplied = context.set_value(ENABLE_CONTENT_TRACING_KEY, True)
            parent = trace.get_tracer("pipecat.example").start_span(
                "pipecat.ambient_parent",
                context=supplied,
                attributes={
                    RESPAN_LOG_TYPE: LOG_TYPE_TASK,
                    RESPAN_LOG_METHOD: LogMethodChoices.PYTHON_TRACING.value,
                    TL.TRACELOOP_ENTITY_NAME: "pipecat.ambient_parent",
                    TL.TRACELOOP_ENTITY_PATH: "pipecat.ambient_parent",
                },
            )
            permit = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, True))
            try:
                with trace.use_span(parent, end_on_exit=True):
                    collector, _ = await run(
                        messages=[
                            {"role": "user", "content": "PRIVATE_AMBIENT_PARENT_PROMPT"}
                        ]
                    )
            finally:
                context.detach(permit)
        finally:
            context.detach(private)
        return {
            "native_frames_preserved": any(
                getattr(f, "text", None) == "Actual native text."
                for f in collector.frames
            )
        }

    try:
        with attributes("ambient-supplied-parent", run_id):
            result = await scenario()
        print_result("ambient-supplied-parent", result, run_id)
    finally:
        finish_respan(sdk)


if __name__ == "__main__":
    asyncio.run(main())
