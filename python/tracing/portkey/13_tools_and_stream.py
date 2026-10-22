import json

from _shared import (
    example_attributes,
    execution_id,
    finish_respan,
    make_client,
    make_respan,
    marker,
    print_result,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "tools-and-stream"


@workflow(name=workflow_name(EXAMPLE_NAME))
def trace_tools(prompt: str):
    client = make_client()
    tools = [
        {
            "type": "function",
            "function": {
                "name": "weather" if i == 0 else f"tool{i}",
                "parameters": {
                    "type": "object",
                    "properties": {f"field{j}": {"type": "string"} for j in range(120)},
                },
            },
        }
        for i in range(65)
    ]
    tools[0]["function"]["parameters"]["properties"]["api_key"] = {"type": "string"}
    try:
        stream = client.chat.completions.create(
            model="fixture-model",
            messages=[{"role": "user", "content": prompt}],
            tools=tools,
            stream=True,
            stream_options={"include_usage": True},
        )
        arguments = ""
        call_id = None
        for chunk in stream:
            if not chunk.choices:
                continue
            for call in chunk.choices[0].delta.tool_calls or []:
                call_id = call.id or call_id
                arguments += call.function.arguments or ""
        return {
            "native_call_id": call_id,
            "arguments": json.loads(arguments),
            "tool_definitions": len(tools),
        }
    finally:
        client.close()


def main():
    run = marker()
    respan = make_respan(EXAMPLE_NAME, run)
    try:
        with example_attributes(EXAMPLE_NAME, run, execution_id(), mode="fixture"):
            print_result(EXAMPLE_NAME, run, trace_tools("Choose a weather tool."))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
