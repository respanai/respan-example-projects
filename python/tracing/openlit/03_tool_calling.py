from __future__ import annotations

import json

from _shared import (
    create_respan,
    example_scope,
    finish_respan,
    provider_config,
    sync_client,
    tool,
    workflow,
)

SCENARIO = "tool-calling"
TOOL_SCHEMA = {
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


@tool(name="get_weather")
def get_weather(city: str) -> str:
    return f"Sunny and 22 C in {city}"


def run_workflow(config) -> str:
    client = sync_client(config)

    @workflow(name="openlit_tool_calling_workflow")
    def traced_workflow(city: str) -> str:
        messages: list[dict] = [
            {
                "role": "user",
                "content": f"Use get_weather for {city}, then answer briefly.",
            }
        ]
        first = client.chat.completions.create(
            model=config.model,
            messages=messages,
            tools=[TOOL_SCHEMA],
            tool_choice={"type": "function", "function": {"name": "get_weather"}},
        )
        assistant = first.choices[0].message
        calls = assistant.tool_calls or []
        if not calls:
            raise RuntimeError("The OpenLIT tool example expected a tool call.")
        messages.append(assistant.model_dump(exclude_none=True))
        for call in calls:
            arguments = json.loads(call.function.arguments or "{}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": get_weather(city=arguments.get("city", city)),
                }
            )
        final = client.chat.completions.create(model=config.model, messages=messages)
        return final.choices[0].message.content or ""

    try:
        return traced_workflow(city="Tokyo")
    finally:
        client.close()


def main() -> None:
    respan = create_respan(SCENARIO)
    try:
        with provider_config() as config, example_scope(SCENARIO):
            print(f"{SCENARIO}: {run_workflow(config)}", flush=True)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
