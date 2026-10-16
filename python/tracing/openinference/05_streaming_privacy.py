from __future__ import annotations

import json

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
from openinference.semconv.trace import SpanAttributes as OISpanAttributes

EXAMPLE_NAME = "streaming-privacy"


@workflow(name=workflow_name(EXAMPLE_NAME))
def streaming_privacy_workflow(description: str) -> str:
    chunks = ("bounded ", "streaming ", "content")
    response = "".join(chunks)
    with tracer().start_as_current_span("openai.chat.stream") as span:
        span.set_attribute("openinference.span.kind", "LLM")
        span.set_attribute(
            OISpanAttributes.LLM_INVOCATION_PARAMETERS,
            json.dumps({"stream": True}),
        )
        span.set_attribute("llm.model_name", "gpt-4.1-mini")
        span.set_attribute("llm.system", "openai")
        span.set_attribute("llm.provider", "openai")
        span.set_attribute(
            "input.value",
            json.dumps(
                {
                    "description": description,
                    "authorization": "Bearer example-secret-must-be-redacted",
                    "nested": {"api_key": "sk-example-secret-123456"},
                }
            ),
        )
        span.set_attribute("output.value", json.dumps({"response": response}))
        span.set_attribute("llm.output_messages.0.message.role", "assistant")
        span.set_attribute("llm.output_messages.0.message.content", response)
        span.set_attribute("llm.token_count.prompt", 7)
        span.set_attribute("llm.token_count.completion", 3)
        span.set_attribute("llm.token_count.total", 10)
    return response


def run() -> None:
    run_id = example_run_id()
    respan = make_respan(EXAMPLE_NAME, run_id)
    result = ""
    try:
        with example_attributes(EXAMPLE_NAME, run_id):
            result = streaming_privacy_workflow(
                "validate a streaming span without exporting credentials"
            )
    finally:
        finish_respan(respan)
    print_result(EXAMPLE_NAME, run_id, result)


if __name__ == "__main__":
    run()
