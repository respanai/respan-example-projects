"""Explicit context and before-detach bounds survive delayed native streams."""

import json

import httpx
from _shared import create_respan, finish_respan
from openai import OpenAI
from opentelemetry import context, trace
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def transport(request):
    if json.loads(request.content).get("stream"):
        chunks = [
            {
                "id": "fixture",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": "fixture",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": "PRIVATE_STREAM"},
                        "finish_reason": None,
                    }
                ],
            },
            {
                "id": "fixture",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": "fixture",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            },
        ]
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content="".join("data: " + json.dumps(c) + "\n\n" for c in chunks)
            + "data: [DONE]\n\n",
        )
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
                    "message": {"role": "assistant", "content": "PRIVATE_OUTPUT"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
        },
    )


def main():
    telemetry = create_respan("parent-privacy")
    client = OpenAI(
        api_key="fixture",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(transport)),
    )
    caller = telemetry.provider.get_tracer("caller")
    try:
        parent = caller.start_span(
            "explicit-private-parent",
            context=context.set_value(ENABLE_CONTENT_TRACING_KEY, False),
        )
        token = context.attach(trace.set_span_in_context(parent))
        try:
            client.chat.completions.create(
                model="fixture",
                messages=[{"role": "user", "content": "PRIVATE_CONTEXT"}],
            )
        finally:
            context.detach(token)
            parent.end()
        with caller.start_as_current_span("delayed-parent"):
            stream = client.chat.completions.create(
                model="fixture",
                messages=[{"role": "user", "content": "PRIVATE_DELAYED"}],
                stream=True,
            )
            next(stream)
            context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        list(stream)
        assert "PRIVATE_" not in json.dumps(
            [dict(s.attributes) for s in telemetry.exporter.get_finished_spans()]
        )
        print("native values preserved; two child bounds remain private")
    finally:
        client.close()
        finish_respan(telemetry)


if __name__ == "__main__":
    main()
