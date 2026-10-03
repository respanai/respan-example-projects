"""Deterministic real-SDK fixtures and Respan setup."""

import asyncio
import json
import os
from pathlib import Path
from uuid import uuid4

from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from openai import AsyncOpenAI
from respan import Respan, propagate_attributes, workflow
from respan_instrumentation_autogen import AutoGenInstrumentor

try:
    import httpx2 as httpx
except ImportError:
    import httpx

MODEL = "gpt-4o-mini-2024-07-18"
CLIENTS = []


def response(content="Fixture answer.", calls=None):
    message = {"role": "assistant", "content": content}
    if calls:
        message["content"] = None
        message["tool_calls"] = [
            {
                "id": ident,
                "type": "function",
                "function": {"name": name, "arguments": arguments},
            }
            for ident, name, arguments in calls
        ]
    return {
        "id": "autogen-fixture",
        "object": "chat.completion",
        "created": 1,
        "model": MODEL,
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": "tool_calls" if calls else "stop",
            }
        ],
        "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
    }


def chunk(text=None, terminal=False):
    value = {
        "id": "fixture",
        "object": "chat.completion.chunk",
        "created": 1,
        "model": MODEL,
        "choices": []
        if terminal
        else [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
    }
    if terminal:
        value["usage"] = {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}
    return ("data: " + json.dumps(value) + "\n\n").encode()


class StreamFixture(httpx.AsyncByteStream):
    def __init__(self, mode="complete"):
        self.mode = mode
        self.waiting = asyncio.Event()

    async def __aiter__(self):
        yield chunk("Fixture ")
        if self.mode == "error":
            raise httpx.ReadError("Controlled AutoGen stream failure")
        if self.mode == "cancel":
            self.waiting.set()
            await asyncio.Event().wait()
        yield chunk("stream answer.")
        yield chunk(terminal=True)
        yield b"data: [DONE]\n\n"


async def client(*responses, stream=None):
    queue = list(responses) or [response()]

    def handler(request):
        if stream is not None:
            return httpx.Response(
                200, headers={"content-type": "text/event-stream"}, stream=stream
            )
        payload = queue.pop(0)
        if isinstance(payload, int):
            return httpx.Response(
                payload,
                json={
                    "error": {
                        "message": "Controlled AutoGen provider failure",
                        "type": "fixture",
                    }
                },
            )
        return httpx.Response(200, json=payload)

    model = OpenAIChatCompletionClient(model=MODEL, api_key="fixture")
    await model._client.close()
    model._client = AsyncOpenAI(
        api_key="fixture",
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    CLIENTS.append(model)
    return model


def run(name, scenario, *, api="agentchat"):
    load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID") or f"autogen-{uuid4().hex[:12]}"
    runtime = Respan(
        api_key=os.environ["RESPAN_API_KEY"],
        base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
        is_auto_instrument=False,
        instrumentations=[AutoGenInstrumentor(api=api)],
        metadata={"run_id": marker, "example_set": "autogen", "scenario": name},
    )

    @workflow(name=f"autogen-{name}")
    async def execute():
        try:
            return await scenario()
        finally:
            for model in CLIENTS:
                await model.close()

    try:
        with propagate_attributes(
            custom_identifier=marker, metadata={"run_id": marker, "scenario": name}
        ):
            print(asyncio.run(execute()))
        runtime.flush()
    finally:
        runtime.shutdown()
    print(f"RESPAN_EXAMPLE_RUN_ID={marker}")
