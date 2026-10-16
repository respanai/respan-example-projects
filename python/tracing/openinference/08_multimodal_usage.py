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

EXAMPLE_NAME = "multimodal-usage"


@workflow(name=workflow_name(EXAMPLE_NAME))
def work():
    native = OITracer(tracer(), config=TraceConfig())
    with native.start_as_current_span(
        "multimodal", openinference_span_kind="llm"
    ) as span:
        span.set_attribute("llm.request.model_name", "requested-model")
        span.set_attribute("llm.response.model_name", "returned-model")
        span.set_attribute("llm.model_name", "fixture-model")
        span.set_attribute("llm.input_messages.0.message.role", "user")
        span.set_attribute(
            "llm.input_messages.0.message.contents.0.message_content.type", "text"
        )
        span.set_attribute(
            "llm.input_messages.0.message.contents.0.message_content.text",
            "describe the fixture",
        )
        span.set_attribute(
            "llm.input_messages.0.message.contents.1.message_content.type", "image"
        )
        span.set_attribute(
            "llm.input_messages.0.message.contents.1.message_content.image.image.url",
            "https://fixture.invalid/image.png",
        )
        span.set_attribute("llm.output_messages.0.message.role", "assistant")
        span.set_attribute(
            "llm.output_messages.0.message.content", "image fixture description"
        )
        span.set_attribute("llm.token_count.prompt", 11)
        span.set_attribute("llm.token_count.completion", 7)
        span.set_attribute("llm.token_count.total", 18)
        span.set_attribute("llm.token_count.prompt_details.cache_read", 3)
        span.set_attribute("llm.token_count.prompt_details.cache_write", 4)
        span.set_attribute("llm.token_count.completion_details.reasoning", 2)
    return "typed text/image content and provider-sourced cache/reasoning usage"


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
