from __future__ import annotations

import json

from _shared import (
    example_attributes,
    make_client,
    make_custom_identifier,
    make_respan,
    model_name,
    print_result,
    set_workflow_input,
    workflow_name,
)
from opentelemetry import trace
from opentelemetry.semconv._incubating.attributes.gen_ai_attributes import (
    GEN_AI_TOOL_CALL_ID,
)
from respan import tool, workflow

EXAMPLE_NAME = "tool-calling"


def _weather_tool_schema() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Return deterministic weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name for the weather lookup.",
                    }
                },
                "required": ["city"],
            },
        },
    }


@tool(name="get_weather")
def get_weather(city: str, tool_call_id: str | None = None) -> str:
    if tool_call_id:
        trace.get_current_span().set_attribute(GEN_AI_TOOL_CALL_ID, tool_call_id)
    return f"Sunny and 22 C in {city}"


@workflow(name=workflow_name(EXAMPLE_NAME))
def _tool_calling_workflow(client) -> str:
    prompt = "What is the weather in Tokyo? Use the tool and answer briefly."
    set_workflow_input(prompt)
    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]
    response = client.chat.completions.create(
        model=model_name(),
        messages=messages,
        tools=[_weather_tool_schema()],
        tool_choice={"type": "function", "function": {"name": "get_weather"}},
        temperature=0,
    )
    message = response.choices[0].message
    tool_calls = message.tool_calls or []

    if not tool_calls:
        return get_weather(city="Tokyo")

    assistant_message = message.model_dump(exclude_none=True)
    messages.append(assistant_message)
    for tool_call in tool_calls:
        arguments = json.loads(tool_call.function.arguments or "{}")
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": get_weather(
                    city=arguments.get("city", "Tokyo"), tool_call_id=tool_call.id
                ),
            }
        )

    follow_up = client.chat.completions.create(
        model=model_name(),
        messages=messages,
        temperature=0,
    )
    return follow_up.choices[0].message.content or ""


def run_tool_calling() -> None:
    respan = make_respan(EXAMPLE_NAME)
    client = make_client()
    custom_identifier = make_custom_identifier(EXAMPLE_NAME)
    text = ""

    try:
        with example_attributes(EXAMPLE_NAME, custom_identifier):
            print(f"custom_identifier={custom_identifier}", flush=True)
            print(f"workflow_name={workflow_name(EXAMPLE_NAME)}", flush=True)
            text = _tool_calling_workflow(client)
    finally:
        client.close()
        respan.shutdown()

    print_result(EXAMPLE_NAME, custom_identifier, text)


if __name__ == "__main__":
    run_tool_calling()
