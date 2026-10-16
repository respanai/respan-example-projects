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

EXAMPLE_NAME = "tool-call"
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "lookup_weather",
        "description": "Return deterministic weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}


@workflow(name=workflow_name(EXAMPLE_NAME))
def tool_call_workflow(city: str) -> str:
    call_id = "call-weather-001"
    arguments = json.dumps({"city": city})
    result = {
        "city": city,
        "temperature_c": 22,
        "condition": "sunny",
        "vector": [i / 10000 for i in range(5000)],
    }

    with tracer().start_as_current_span("openai.chat.tool_call") as chat_span:
        chat_span.set_attribute("openinference.span.kind", "LLM")
        chat_span.set_attribute("llm.model_name", "gpt-4.1-mini")
        chat_span.set_attribute("llm.system", "openai")
        chat_span.set_attribute("llm.provider", "openai")
        chat_span.set_attribute("llm.tools", json.dumps([TOOL_DEFINITION]))
        chat_span.set_attribute("llm.input_messages.0.message.role", "user")
        chat_span.set_attribute(
            "llm.input_messages.0.message.content",
            f"What is the weather in {city}?",
        )
        chat_span.set_attribute("llm.output_messages.0.message.role", "assistant")
        chat_span.set_attribute(
            "llm.output_messages.0.message.tool_calls.0.tool_call.id",
            call_id,
        )
        chat_span.set_attribute(
            "llm.output_messages.0.message.tool_calls.0.tool_call.function.name",
            "lookup_weather",
        )
        chat_span.set_attribute(
            "llm.output_messages.0.message.tool_calls.0.tool_call.function.arguments",
            arguments,
        )
        chat_span.set_attribute("llm.token_count.prompt", 18)
        chat_span.set_attribute("llm.token_count.completion", 6)
        chat_span.set_attribute("llm.token_count.total", 24)

        with tracer().start_as_current_span("lookup_weather") as tool_span:
            tool_span.set_attribute("openinference.span.kind", "TOOL")
            tool_span.set_attribute("tool.name", "lookup_weather")
            tool_span.set_attribute("tool.id", call_id)
            tool_span.set_attribute("input.value", arguments)
            tool_span.set_attribute("output.value", json.dumps(result))
    return f"weather result includes complete {len(result['vector'])}-dimension vector"


def run() -> None:
    run_id = example_run_id()
    respan = make_respan(EXAMPLE_NAME, run_id)
    result = ""
    try:
        with example_attributes(EXAMPLE_NAME, run_id):
            result = tool_call_workflow("Tokyo")
    finally:
        finish_respan(respan)
    print_result(EXAMPLE_NAME, run_id, result)


if __name__ == "__main__":
    run()
