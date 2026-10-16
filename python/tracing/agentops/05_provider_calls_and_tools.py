"""Current declarations stay on model spans; actual decorated tools execute."""

import asyncio
import json

from _fixtures import provider_clients
from _shared import build_respan
from agentops import tool
from agentops import trace as agentops_trace
from opentelemetry import trace
from opentelemetry.semconv._incubating.attributes.gen_ai_attributes import (
    GEN_AI_TOOL_CALL_ID,
)


def main():
    telemetry = build_respan(
        example_name="provider-tools", workflow_name="agentops_provider_tools"
    )
    sdk, client, async_client = provider_clients()

    @tool(name="vector_tool")
    def vector_tool(label, vector, source_call_id):
        trace.get_current_span().set_attribute(GEN_AI_TOOL_CALL_ID, source_call_id)
        return {
            "label": label,
            "dense": vector,
            "sparse": {i * 2: i / 256 for i in range(256)},
        }

    @agentops_trace(name="provider_workflow")
    def run():
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "vector_tool",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "vector": {"type": "array", "items": {"type": "number"}},
                        },
                    },
                },
            }
        ]
        response = client.chat.completions.create(
            model="fixture-chat",
            messages=[
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
                    "content": "old result",
                    "tool_call_id": "history-only",
                },
                {"role": "user", "content": "Return two vectors"},
            ],
            tools=tools,
        )
        actual = response.choices[0].message.tool_calls
        results = [
            vector_tool(**json.loads(c.function.arguments), source_call_id=c.id)
            for c in actual
        ]
        assert len(actual) == 2 and all(
            len(r["dense"]) == 5000 and len(r["sparse"]) == 256 for r in results
        )
        return {
            "actual_call_ids": [c.id for c in actual],
            "dimensions": [len(r["dense"]) for r in results],
        }

    try:
        print(run())
    finally:
        sdk.uninstrument()
        client.close()
        asyncio.run(async_client.close())
        telemetry.shutdown()


if __name__ == "__main__":
    main()
