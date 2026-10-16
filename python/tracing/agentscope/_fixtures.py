"""Synthetic HTTP fixtures consumed by the real AgentScope provider models."""

import json

import httpx2
from agentscope.credential import OpenAICredential
from agentscope.embedding import OpenAIEmbeddingModel
from agentscope.model import OpenAIChatModel
from openai import AsyncOpenAI


class Fixture:
    def __init__(self):
        self.requests = []
        self.clients = []

    async def handle(self, request):
        body = json.loads(request.content)
        self.requests.append(body)
        if "fixture-failure" in json.dumps(body):
            return httpx2.Response(
                400,
                json={
                    "error": {
                        "message": "controlled fixture error",
                        "type": "invalid_request_error",
                    }
                },
            )
        if request.url.path.endswith("/embeddings"):
            return httpx2.Response(
                200,
                json={
                    "object": "list",
                    "model": "fixture-embedding",
                    "data": [
                        {
                            "index": i,
                            "object": "embedding",
                            "embedding": [float(n) for n in range(256)],
                        }
                        for i, _ in enumerate(body["input"])
                    ],
                    "usage": {"prompt_tokens": 7, "total_tokens": 7},
                },
            )
        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "prompt_tokens_details": {"cached_tokens": 0},
        }
        message = {"role": "assistant", "content": "fixture answer"}
        if body.get("tools") and not any(m["role"] == "tool" for m in body["messages"]):
            name = body["tools"][0]["function"]["name"]
            arguments = (
                {"city": "Tokyo"}
                if name != "generate_structured_output"
                else {"answer": "fixture value"}
            )
            message = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "fixture-tool-id",
                        "type": "function",
                        "function": {"name": name, "arguments": json.dumps(arguments)},
                    }
                ],
            }
        base = {"id": "fixture-response", "created": 0, "model": "fixture-chat"}
        if body.get("stream"):
            chunks = [
                {
                    **base,
                    "object": "chat.completion.chunk",
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
                    "object": "chat.completion.chunk",
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
                    "object": "chat.completion.chunk",
                    "choices": [],
                    "usage": usage,
                },
            ]
            return httpx2.Response(
                200,
                text="".join("data: " + json.dumps(x) + "\n\n" for x in chunks)
                + "data: [DONE]\n\n",
                headers={"content-type": "text/event-stream"},
            )
        return httpx2.Response(
            200,
            json={
                **base,
                "object": "chat.completion",
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
        client = AsyncOpenAI(
            api_key="fixture-only",
            base_url="https://fixture.invalid/v1",
            http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(self.handle)),
            max_retries=0,
        )
        self.clients.append(client)
        return client

    def model(self, stream=False):
        model = OpenAIChatModel(
            credential=OpenAICredential(
                api_key="fixture-only", base_url="https://fixture.invalid/v1"
            ),
            model="fixture-chat",
            stream=stream,
            max_retries=0,
            client_kwargs={
                "http_client": httpx2.AsyncClient(
                    transport=httpx2.MockTransport(self.handle)
                ),
                "max_retries": 0,
            },
        )
        self.clients.append(model.client)
        return model

    def embedding(self):
        model = OpenAIEmbeddingModel(
            credential=OpenAICredential(
                api_key="fixture-only", base_url="https://fixture.invalid/v1"
            ),
            model="fixture-embedding",
            dimensions=256,
            max_retries=0,
        )
        model.client = self.client()
        model.batch_size = 2
        return model

    async def close(self):
        for client in self.clients:
            await client.close()
