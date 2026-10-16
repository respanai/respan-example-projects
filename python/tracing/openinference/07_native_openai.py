"""Native OI OpenAI delegate: controlled HTTP, SDK responses, streams and error."""

from __future__ import annotations

import json

import httpx
from _shared import (
    example_attributes,
    example_run_id,
    finish_respan,
    make_respan,
    print_result,
    workflow,
    workflow_name,
)
from openai import APIStatusError, OpenAI, Stream
from openinference.instrumentation.openai import OpenAIInstrumentor

EXAMPLE_NAME = "native-openai"


@workflow(name=workflow_name(EXAMPLE_NAME))
def work():
    payload = {
        "id": "fixture-response",
        "object": "chat.completion",
        "created": 1,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "native fixture answer"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 11,
            "completion_tokens": 7,
            "total_tokens": 18,
            "prompt_tokens_details": {"cached_tokens": 3},
            "completion_tokens_details": {"reasoning_tokens": 2},
        },
    }

    def handler(request):
        body = json.loads(request.content)
        if body["messages"][0]["content"] == "controlled failure":
            return httpx.Response(
                401,
                json={
                    "error": {
                        "message": "controlled fixture error",
                        "type": "authentication_error",
                    }
                },
            )
        if body.get("stream"):
            chunk = {
                **payload,
                "object": "chat.completion.chunk",
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": "native fixture answer",
                        },
                        "finish_reason": "stop",
                    }
                ],
            }
            return httpx.Response(
                200,
                text="data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n\n",
                headers={"content-type": "text/event-stream"},
            )
        return httpx.Response(200, json=payload)

    # Keep native clients out of workflow inputs so client credentials cannot be serialized.
    with OpenAI(
        api_key="fixture-only",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        max_retries=0,
    ) as client:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "fixture prompt"}],
        )
        assert response.choices[0].message.content == "native fixture answer"
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "fixture prompt"}],
            stream=True,
        )
        assert isinstance(stream, Stream)
        chunks = list(stream)
        assert chunks[0].choices[0].delta.content == "native fixture answer"
        stream.close()
        try:
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "controlled failure"}],
            )
        except APIStatusError as error:
            assert error.status_code == 401
        else:
            raise AssertionError("expected native401")
    return "native response, native stream chunks, source usage and401 retained"


def run():
    marker = example_run_id()
    telemetry = make_respan(EXAMPLE_NAME, marker)
    telemetry.delegate(OpenAIInstrumentor)
    try:
        with example_attributes(EXAMPLE_NAME, marker):
            result = work()
    finally:
        finish_respan(telemetry)
    print_result(EXAMPLE_NAME, marker, result)


if __name__ == "__main__":
    run()
