"""Synthetic HTTP responses consumed by the real Semantic Kernel/OpenAI SDKs."""

import json

import httpx2 as httpx
from openai import AsyncOpenAI


class FixtureServer:
    def __init__(self):
        self.requests = []

    async def handle(self, request):
        body = json.loads(request.content)
        self.requests.append(body)
        if "fixture-failure" in json.dumps(body):
            return httpx.Response(
                400,
                json={
                    "error": {
                        "message": "controlled fixture failure",
                        "type": "invalid_request_error",
                        "code": "fixture_failure",
                    }
                },
            )
        if request.url.path.endswith("/embeddings"):
            return httpx.Response(
                200,
                json={
                    "object": "list",
                    "model": "fixture-embedding",
                    "data": [
                        {
                            "index": i,
                            "object": "embedding",
                            "embedding": [float(n) for n in range(128)],
                        }
                        for i, _ in enumerate(body["input"])
                    ],
                    "usage": {"prompt_tokens": 7, "total_tokens": 7},
                },
            )
        usage = {
            "prompt_tokens": 9,
            "completion_tokens": 3,
            "total_tokens": 12,
            "prompt_tokens_details": {"cached_tokens": 4},
            "completion_tokens_details": {"reasoning_tokens": 2},
        }
        if body.get("stream"):
            if "empty-stream" in json.dumps(body):
                content = "data: [DONE]\n\n"
            else:
                base = {
                    "id": "fixture-stream",
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": "fixture-model",
                }
                chunks = [
                    {
                        **base,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"role": "assistant", "content": "fixture "},
                                "finish_reason": None,
                            }
                        ],
                    },
                    {
                        **base,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": "stream"},
                                "finish_reason": "stop",
                            }
                        ],
                    },
                    {
                        **base,
                        "choices": [],
                        "usage": {
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "total_tokens": 0,
                            "prompt_tokens_details": {"cached_tokens": 0},
                            "completion_tokens_details": {"reasoning_tokens": 0},
                        },
                    },
                ]
                content = (
                    "".join("data: " + json.dumps(chunk) + "\n\n" for chunk in chunks)
                    + "data: [DONE]\n\n"
                )
            return httpx.Response(
                200, text=content, headers={"content-type": "text/event-stream"}
            )
        message = {"role": "assistant", "content": "fixture answer"}
        if body.get("tools") and not any(
            row["role"] == "tool" for row in body["messages"]
        ):
            message = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "fixture-tool-id",
                        "type": "function",
                        "function": {
                            "name": body["tools"][0]["function"]["name"],
                            "arguments": '{"city":"Tokyo"}',
                        },
                    }
                ],
            }
        return httpx.Response(
            200,
            json={
                "id": "fixture-response",
                "object": "chat.completion",
                "created": 0,
                "model": "fixture-model",
                "choices": [
                    {
                        "index": 0,
                        "message": message,
                        "finish_reason": "tool_calls"
                        if message.get("tool_calls")
                        else "stop",
                    }
                ],
                "usage": usage,
            },
        )

    def client(self):
        return AsyncOpenAI(
            api_key="fixture-only",
            base_url="https://fixture.invalid/v1",
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(self.handle)),
            max_retries=0,
        )
