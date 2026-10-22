from __future__ import annotations

import json
from typing import Any

from _shared import (
    example_attributes,
    finish_respan,
    first_message_text,
    make_client,
    make_custom_identifier,
    make_respan,
    model_name,
    print_result,
    print_start,
    workflow_name,
)
from respan import tool, workflow

EXAMPLE_NAME = "tool-calling"


@tool(name="get_weather")
def get_weather(city: str) -> str:
    return f"Sunny and 22 C in {city}"


def _run_tool_call(tool_call: Any) -> dict[str, str]:
    function = getattr(tool_call, "function", None)
    name = getattr(function, "name", "")
    arguments = getattr(function, "arguments", "{}")
    parsed_arguments = json.loads(arguments or "{}")
    if name != "get_weather":
        return {"name": name, "result": f"Unsupported tool: {name}"}
    return {
        "name": name,
        "result": get_weather(city=parsed_arguments.get("city", "Tokyo")),
    }


@workflow(name=workflow_name(EXAMPLE_NAME))
def _tool_calling_workflow(city: str) -> str:
    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": f"What is the weather in {city}? Use the tool when available.",
        }
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Return deterministic weather for a city.",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }
    ]
    with make_client() as client:
        response = client.chat.completions.create(
            model=model_name(),
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=160,
            temperature=0,
        )
        first_choice = (getattr(response, "choices", None) or [None])[0]
        message = getattr(first_choice, "message", None)
        tool_calls = getattr(message, "tool_calls", None) or []
        if not tool_calls:
            return first_message_text(response)

        messages.append(
            {
                "role": "assistant",
                "content": getattr(message, "content", "") or "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in tool_calls
                ],
            }
        )
        for tool_call in tool_calls:
            tool_result = _run_tool_call(tool_call)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result["result"],
                }
            )

        final_response = client.chat.completions.create(
            model=model_name(),
            messages=messages,
            tools=tools,
            max_tokens=120,
            temperature=0,
        )
        return first_message_text(final_response)


def run_tool_calling() -> None:
    custom_identifier = make_custom_identifier(EXAMPLE_NAME)
    respan = make_respan(EXAMPLE_NAME, custom_identifier)
    text = ""

    try:
        with example_attributes(EXAMPLE_NAME, custom_identifier):
            print_start(EXAMPLE_NAME, custom_identifier)
            text = _tool_calling_workflow("Tokyo")
    finally:
        finish_respan(respan)

    print_result(EXAMPLE_NAME, custom_identifier, text)


if __name__ == "__main__":
    run_tool_calling()
