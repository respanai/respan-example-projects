"""Actual two current declarations, history, schemas, executed dense/sparse tools."""

import json

import httpx
from _shared import create_respan, finish_respan, tool, workflow
from openai import OpenAI
from opentelemetry import trace
from opentelemetry.semconv._incubating.attributes.gen_ai_attributes import (
    GEN_AI_TOOL_CALL_ID,
)


def transport(request):
    calls = [
        {
            "id": f"current-vector-{i}",
            "type": "function",
            "function": {
                "name": "vector_tool",
                "arguments": json.dumps(
                    {
                        "dense": list(range(5000)),
                        "sparse": {j * 2: j / 256 for j in range(256)},
                    }
                ),
            },
        }
        for i in range(2)
    ]
    return httpx.Response(
        200,
        json={
            "id": "fixture",
            "object": "chat.completion",
            "created": 1,
            "model": "fixture",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": calls,
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {
                "prompt_tokens": 11,
                "completion_tokens": 7,
                "total_tokens": 18,
                "prompt_tokens_details": {"cached_tokens": 3},
                "completion_tokens_details": {"reasoning_tokens": 2},
            },
        },
    )


@tool(name="vector_tool")
def vector_tool(dense, sparse, source_call_id):
    trace.get_current_span().set_attribute(GEN_AI_TOOL_CALL_ID, source_call_id)
    return {"dense": dense, "sparse": sparse}


def main():
    telemetry = create_respan("full-tool-payloads")
    client = OpenAI(
        api_key="fixture",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(transport)),
    )

    @workflow(name="full_tool_payloads")
    def run():
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "vector_tool",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dense": {"type": "array", "items": {"type": "number"}},
                            "sparse": {"type": "object"},
                            "api_key": {
                                "type": "string",
                                "default": "SYNTHETIC_CREDENTIAL",
                                "examples": ["SYNTHETIC_EXAMPLE"],
                            },
                            **{f"field{i}": {"type": "number"} for i in range(120)},
                        },
                    },
                },
            }
        ]
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "history-only",
                        "type": "function",
                        "function": {"name": "old", "arguments": '{"x":1}'},
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "history-only",
                "content": json.dumps({"vector": list(range(5000))}),
            },
            {"role": "user", "content": "two controlled vectors"},
        ]
        result = client.chat.completions.create(
            model="fixture", messages=messages, tools=tools
        )
        actual = result.choices[0].message.tool_calls
        outputs = [
            vector_tool(**json.loads(c.function.arguments), source_call_id=c.id)
            for c in actual
        ]
        assert len(outputs) == 2 and all(
            len(o["dense"]) == 5000 and len(o["sparse"]) == 256 for o in outputs
        )
        return {
            "actual_ids": [c.id for c in actual],
            "dense_dimensions": 5000,
            "sparse_dimensions": 256,
        }

    try:
        print(run())
    finally:
        client.close()
        finish_respan(telemetry)


if __name__ == "__main__":
    main()
