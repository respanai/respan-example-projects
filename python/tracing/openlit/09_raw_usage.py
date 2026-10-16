"""Provider booleans never become reported zero token usage after SDK coercion."""

import httpx
from _shared import create_respan, finish_respan, workflow
from openai import OpenAI


def transport(request):
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
                    "message": {"role": "assistant", "content": "actual value"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": False,
                "completion_tokens": False,
                "total_tokens": False,
            },
        },
    )


def main():
    telemetry = create_respan("raw-usage")
    client = OpenAI(
        api_key="fixture",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(transport)),
    )

    @workflow(name="raw_usage")
    def run():
        result = client.chat.completions.create(
            model="fixture", messages=[{"role": "user", "content": "controlled"}]
        )
        assert result.choices[0].message.content == "actual value"
        return "native result preserved"

    try:
        print(run())
        spans = telemetry.exporter.get_finished_spans()
        assert all(not any("usage" in k for k in s.attributes) for s in spans)
    finally:
        client.close()
        finish_respan(telemetry)


if __name__ == "__main__":
    main()
