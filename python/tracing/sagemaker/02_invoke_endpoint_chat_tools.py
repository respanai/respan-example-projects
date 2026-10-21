import json

from _native import client
from _shared import Runtime

runtime = Runtime("02_chat_tools")
payload = {
    "model": "controlled-model",
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "native tool result",
                "tool_calls": [
                    {
                        "id": "controlled-tool-id",
                        "type": "function",
                        "function": {
                            "name": "lookup",
                            "arguments": json.dumps(
                                {"history": list(range(75)), "false": False, "zero": 0}
                            ),
                        },
                    }
                ],
            }
        }
    ],
    "usage": {"input_tokens": 0, "output_tokens": 2, "total_tokens": 0},
}
request = {
    "messages": [{"role": "user", "content": f"history-{i}"} for i in range(75)],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "lookup",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "default": "controlled credential",
                        },
                        "vector": {"type": "array", "items": {"type": "number"}},
                    },
                },
            },
        }
    ],
}
try:
    with runtime.workflow():
        c, _, _ = client(payload)
        try:
            result = c.invoke_endpoint(
                EndpointName="controlled-endpoint",
                Body=json.dumps(request).encode(),
                ContentType="application/json",
            )
            assert json.loads(result["Body"].read()) == payload
            result["Body"].close()
        finally:
            c.close()
finally:
    runtime.close()
