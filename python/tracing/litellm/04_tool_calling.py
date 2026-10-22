import os

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import json

import litellm
from _shared import (
    GATEWAY_API_KEY,
    GATEWAY_BASE_URL,
    MODEL,
    create_respan,
    provider_client,
    run_with_example_attributes,
)
from respan import workflow

WORKFLOW_NAME = "litellm_tool_calling.workflow"
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get deterministic weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }
]


@workflow(name=WORKFLOW_NAME)
def litellm_tool_calling() -> list[dict[str, object]]:
    response = litellm.completion(
        **provider_client(tools=True),
        api_key=GATEWAY_API_KEY,
        api_base=GATEWAY_BASE_URL,
        model=MODEL,
        messages=[{"role": "user", "content": "What is the weather in Paris?"}],
        tools=TOOLS,
        tool_choice={"type": "function", "function": {"name": "get_weather"}},
        temperature=0,
        max_tokens=80,
    )
    calls = response.choices[0].message.tool_calls or []
    if not calls:
        raise RuntimeError("The provider returned no tool call.")
    return [
        call.model_dump() if hasattr(call, "model_dump") else dict(call)
        for call in calls
    ]


def main() -> None:
    respan = create_respan("litellm-tool-calling")
    try:
        output = run_with_example_attributes(
            respan,
            workflow_name=WORKFLOW_NAME,
            action=litellm_tool_calling,
        )
        print(json.dumps(output, default=str))
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
