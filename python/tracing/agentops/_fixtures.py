"""Actual AgentOps/OpenAI SDK with controlled HTTP and SSE."""

import json

import httpx


def provider_response(request):
    body = json.loads(request.content)
    if request.url.path.endswith("/embeddings"):
        return httpx.Response(
            200,
            json={
                "object": "list",
                "model": "fixture-embedding",
                "data": [
                    {
                        "object": "embedding",
                        "index": 0,
                        "embedding": [i / 5000 for i in range(5000)],
                    }
                ],
                "usage": {"prompt_tokens": 13, "total_tokens": 13},
            },
        )
    if "FAIL_PROVIDER" in json.dumps(body.get("messages")):
        return httpx.Response(
            503,
            json={
                "error": {
                    "message": "controlled provider failure",
                    "type": "server_error",
                    "code": "fixture",
                }
            },
        )
    usage = {
        "prompt_tokens": 11,
        "completion_tokens": 7,
        "total_tokens": 18,
        "prompt_tokens_details": {"cached_tokens": 3},
        "completion_tokens_details": {"reasoning_tokens": 2},
    }
    if body.get("stream"):
        parts = [
            {
                "id": "fixture",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": "fixture-chat",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": "answer"},
                        "finish_reason": None,
                    }
                ],
            },
            {
                "id": "fixture",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": "fixture-chat",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                "usage": usage,
            },
        ]
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content="".join("data: " + json.dumps(p) + "\n\n" for p in parts)
            + "data: [DONE]\n\n",
        )
    message = {"role": "assistant", "content": "answer"}
    if body.get("tools"):
        message["content"] = ""
        message["tool_calls"] = [
            {
                "id": f"actual-call-{i}",
                "type": "function",
                "function": {
                    "name": "vector_tool",
                    "arguments": json.dumps(
                        {"label": str(i), "vector": list(range(5000))}
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
            "model": "fixture-chat",
            "choices": [
                {
                    "index": 0,
                    "message": message,
                    "finish_reason": "tool_calls" if body.get("tools") else "stop",
                }
            ],
            "usage": usage,
        },
    )


def provider_clients():
    import openai
    from agentops.instrumentation.providers.openai import OpenaiInstrumentor

    instrumentor = OpenaiInstrumentor()
    instrumentor.instrument()
    client = openai.OpenAI(
        api_key="fixture-key",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(provider_response)),
    )
    async_client = openai.AsyncOpenAI(
        api_key="fixture-key",
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(provider_response)),
    )
    return instrumentor, client, async_client
