"""Synthetic Groq HTTP fixtures; no model provider request is sent."""

import json

import httpx

MODEL = "fixture-groq-model"
CALL = {
    "id": "call_weather",
    "type": "function",
    "function": {"name": "get_weather", "arguments": '{"city":"Tokyo"}'},
}


def chat_response(request):
    body = json.loads(request.content)
    if body.get("model") == "fixture-error":
        return httpx.Response(
            503,
            json={
                "error": {"message": "synthetic unavailable", "type": "server_error"}
            },
        )
    tool = bool(body.get("tools"))
    if body.get("stream"):
        deltas = (
            [
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "index": 0,
                            "id": "call_weather",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"city":',
                            },
                        }
                    ],
                },
                {"tool_calls": [{"index": 0, "function": {"arguments": '"Tokyo"}'}}]},
            ]
            if tool
            else [{"role": "assistant", "content": "hello "}, {"content": "world"}]
        )
        frames = [
            {
                "id": "chat-fixture",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": MODEL,
                "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
            }
            for delta in deltas
        ]
        frames.append(
            {
                "id": "chat-fixture",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": MODEL,
                "choices": [],
                "x_groq": {
                    "id": "fixture",
                    "usage": {
                        "prompt_tokens": 4,
                        "completion_tokens": 2,
                        "total_tokens": 6,
                    },
                },
            }
        )
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content="".join("data: " + json.dumps(frame) + "\n\n" for frame in frames)
            + "data: [DONE]\n\n",
        )
    return httpx.Response(
        200,
        json={
            "id": "chat-fixture",
            "object": "chat.completion",
            "created": 1,
            "model": MODEL,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None if tool else "hello world",
                        "tool_calls": [CALL] if tool else None,
                    },
                    "finish_reason": "tool_calls" if tool else "stop",
                }
            ],
            "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
        },
    )


def inference_response(request):
    if request.url.path.endswith("/embeddings"):
        body = json.loads(request.content)
        vector = (
            "AACAPwAAAEA=" if body.get("encoding_format") == "base64" else [1.0, 2.0]
        )
        return httpx.Response(
            200,
            json={
                "object": "list",
                "model": MODEL,
                "data": [{"object": "embedding", "index": 0, "embedding": vector}],
                "usage": {"prompt_tokens": 3, "total_tokens": 3},
            },
        )
    if request.url.path.endswith("/speech"):
        return httpx.Response(
            200,
            headers={"content-type": "audio/wav"},
            stream=httpx.ByteStream(b"RIFFsynthetic-audio"),
        )
    return httpx.Response(200, json={"text": "synthetic transcript"})


def response(request):
    if request.url.path.endswith("/chat/completions"):
        return chat_response(request)
    return inference_response(request)
