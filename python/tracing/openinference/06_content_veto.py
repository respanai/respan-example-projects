from __future__ import annotations

from _shared import (
    example_attributes,
    example_run_id,
    finish_respan,
    make_respan,
    print_result,
    tracer,
    workflow,
    workflow_name,
)
from openinference.instrumentation import OITracer, TraceConfig
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY

EXAMPLE_NAME = "content-veto"


@workflow(name=workflow_name(EXAMPLE_NAME))
def work():
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    private = tracer().start_span(
        "private", attributes={"openinference.span.kind": "LLM"}
    )
    context.detach(token)
    private.set_attribute("input.value", "private-start-sentinel")
    private.set_attribute("output.value", "private-result-sentinel")
    private.set_attribute("llm.token_count.prompt", 0)
    private.end()
    final = tracer().start_span(
        "final-veto", attributes={"openinference.span.kind": "LLM"}
    )
    final.set_attribute("input.value", "private-final-sentinel")
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    final.end()
    context.detach(token)
    native = OITracer(tracer(), config=TraceConfig())

    @native.chain
    def private_callback():
        context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        return "private-callback-sentinel"

    assert private_callback() == "private-callback-sentinel"
    return "private start, final and native callback vetoes; zero source usage retained"


def run():
    marker = example_run_id()
    telemetry = make_respan(EXAMPLE_NAME, marker)
    try:
        with example_attributes(EXAMPLE_NAME, marker):
            result = work()
    finally:
        finish_respan(telemetry)
    print_result(EXAMPLE_NAME, marker, result)


if __name__ == "__main__":
    run()
