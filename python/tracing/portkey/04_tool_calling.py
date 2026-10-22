from __future__ import annotations

import json

from _shared import (
    example_attributes,
    execution_id,
    finish_respan,
    make_client,
    make_respan,
    marker,
    model_name,
    print_result,
    workflow_name,
)
from opentelemetry import trace
from opentelemetry.semconv._incubating.attributes.gen_ai_attributes import (
    GEN_AI_TOOL_CALL_ID,
)
from respan import tool, workflow

EXAMPLE_NAME = "tool-calling"


@tool(name="get_weather")
def get_weather(city: str, call_id: str) -> str:
    trace.get_current_span().set_attribute(GEN_AI_TOOL_CALL_ID, call_id)
    return f"{city} is sunny and 72F."


@workflow(name=workflow_name(EXAMPLE_NAME))
def trace_tool(city: str) -> dict[str, str]:
    client = make_client()
    messages: list[dict[str, object]] = [
        {"role": "user", "content": f"What is the weather in {city}?"}
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Return deterministic weather.",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }
    ]
    try:
        first = client.chat.completions.create(
            model=model_name(), messages=messages, tools=tools, tool_choice="auto"
        )
        assistant = first.choices[0].message
        call = assistant.tool_calls[0]
        arguments = json.loads(call.function.arguments)
        result = get_weather(arguments["city"], call.id)
        messages.extend(
            [
                assistant.model_dump(exclude_none=True),
                {"role": "tool", "tool_call_id": call.id, "content": result},
            ]
        )
        second = client.chat.completions.create(
            model=model_name(), messages=messages, tools=tools
        )
        return {
            "tool_result": result,
            "response": second.choices[0].message.content or "",
        }
    finally:
        client.close()


def main() -> None:
    run_marker = marker()
    execution = execution_id()
    respan = make_respan(EXAMPLE_NAME, run_marker)
    try:
        with example_attributes(
            EXAMPLE_NAME, run_marker, execution, mode="deterministic"
        ):
            result = trace_tool("Tokyo")
        print_result(EXAMPLE_NAME, run_marker, result)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
