"""Controlled HTTP responses parsed by the released Strands OpenAI provider."""

from __future__ import annotations

import json

import httpx
from strands.models.openai import OpenAIModel


class FixtureClient(httpx.AsyncClient):
    async def aclose(self) -> None:
        # Strands creates an OpenAI client for every tool-loop turn. MockTransport
        # holds no sockets, so this fixture can share its client between turns.
        pass


def create_fixture_model(*, fail: bool = False) -> OpenAIModel:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if fail:
            raise httpx.ConnectError("controlled provider failure", request=request)
        payload = json.loads(request.content)
        tools = payload.get("tools", [])
        messages = payload.get("messages", [])
        tool_done = any(message.get("role") == "tool" for message in messages)
        name = tools[0]["function"]["name"] if tools and not tool_done else None
        arguments = (
            {"city": "Seattle"}
            if name in {"get_weather", "get_vectors"}
            else {"title": "Trace tip", "action": "Inspect the failed span"}
        )
        delta = {"role": "assistant", "content": "Inspect the failed span."}
        finish = "stop"
        if name:
            delta = {
                "role": "assistant",
                "tool_calls": [
                    {
                        "index": 0,
                        "id": f"fixture-call-{calls}",
                        "type": "function",
                        "function": {"name": name, "arguments": json.dumps(arguments)},
                    }
                ],
            }
            finish = "tool_calls"
        chunk = {
            "id": f"fixture-response-{calls}",
            "object": "chat.completion.chunk",
            "created": 1,
            "model": "fixture-model",
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 4,
                "total_tokens": 16,
                "prompt_tokens_details": {"cached_tokens": 3},
                "completion_tokens_details": {"reasoning_tokens": 2},
            },
        }
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n\n",
        )

    client = FixtureClient(transport=httpx.MockTransport(respond))
    return OpenAIModel(
        model_id="fixture-model",
        client_args={
            "api_key": "fixture-key",
            "base_url": "https://fixture.invalid/v1",
            "max_retries": 0,
            "http_client": client,
        },
    )


def create_fixture_responses_model():
    from strands.models.openai_responses import OpenAIResponsesModel

    def respond(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["stream"] is True
        response = {
            "id": "fixture-response-api",
            "object": "response",
            "created_at": 1,
            "status": "completed",
            "output": [],
            "usage": {
                "input_tokens": 9,
                "output_tokens": 3,
                "total_tokens": 12,
                "input_tokens_details": {"cached_tokens": 2},
                "output_tokens_details": {"reasoning_tokens": 1},
            },
        }
        events = [
            {"type": "response.created", "response": response},
            {
                "type": "response.output_text.delta",
                "delta": "Responses fixture answer.",
                "item_id": "fixture-message",
                "output_index": 0,
                "content_index": 0,
            },
            {"type": "response.completed", "response": response},
        ]
        body = "".join(f"data: {json.dumps(event)}\n\n" for event in events)
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, content=body
        )

    return OpenAIResponsesModel(
        model_id="fixture-responses-model",
        client_args={
            "api_key": "fixture-key",
            "base_url": "https://fixture.invalid/v1",
            "max_retries": 0,
            "http_client": FixtureClient(transport=httpx.MockTransport(respond)),
        },
    )
