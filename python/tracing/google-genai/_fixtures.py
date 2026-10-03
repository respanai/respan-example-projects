"""Deterministic HTTP responses consumed by the released Google Gen AI SDK."""

from __future__ import annotations

import json

import httpx
from google import genai
from google.genai import types
from google.oauth2.credentials import Credentials


def _generate(text: str, *, usage: bool = True) -> dict[str, object]:
    result = {"candidates": [{"content": {"role": "model", "parts": [{"text": text}]}}]}
    if usage:
        result["usageMetadata"] = {
            "promptTokenCount": 7,
            "candidatesTokenCount": 3,
            "totalTokenCount": 10,
        }
    return result


def _respond(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content)
    if "invalid-fixture-model" in request.url.path:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": 400,
                    "message": "Deterministic embedding failure",
                    "status": "INVALID_ARGUMENT",
                }
            },
        )
    if request.url.path.endswith(":predict"):
        return httpx.Response(
            200,
            json={
                "predictions": [
                    {
                        "embeddings": {
                            "values": [0.25, 0.5, 0.75],
                            "statistics": {"token_count": 3, "truncated": False},
                        }
                    }
                    for _ in body["instances"]
                ],
                "metadata": {"billableCharacterCount": 24},
            },
        )
    if "batchEmbedContents" in request.url.path:
        return httpx.Response(
            200,
            json={
                "embeddings": [{"values": [0.25, 0.5, 0.75]} for _ in body["requests"]]
            },
        )
    if "streamGenerateContent" in request.url.path:
        chunks = [_generate("Deterministic ", usage=False), _generate("Gemini stream.")]
        return httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            text="".join("data: " + json.dumps(chunk) + "\n\n" for chunk in chunks),
        )
    if any(tool.get("functionDeclarations") for tool in body.get("tools", [])):
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [
                                {
                                    "functionCall": {
                                        "name": "get_weather",
                                        "args": {"city": "Tokyo"},
                                    }
                                }
                            ],
                        }
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 7,
                    "candidatesTokenCount": 3,
                    "totalTokenCount": 10,
                },
            },
        )
    return httpx.Response(200, json=_generate("Deterministic Gemini answer."))


def make_fixture_client(*, vertex: bool = False) -> genai.Client:
    auth = (
        {
            "vertexai": True,
            "project": "fixture-project",
            "location": "us-central1",
            "credentials": Credentials(token="fixture-token"),
        }
        if vertex
        else {"api_key": "fixture-key"}
    )
    return genai.Client(
        **auth,
        http_options=types.HttpOptions(
            client_args={"transport": httpx.MockTransport(_respond)},
            async_client_args={"transport": httpx.MockTransport(_respond)},
        ),
    )
