"""Real OpenAI SDK controlled HTTP, SSE, async and original error boundaries."""

import asyncio

from _shared import init_telemetry, make_openai_chat_model, tracing_config
from openai import InternalServerError


def main():
    init_telemetry("langchain-provider")
    model = make_openai_chat_model()
    answer = model.invoke("Controlled question", config=tracing_config("provider_http"))
    assert answer.content == "Controlled HTTP answer."
    chunks = list(
        model.stream(
            "Controlled question",
            config=tracing_config("provider_sse"),
            stream_options={"include_usage": True},
        )
    )
    assert "".join(c.content for c in chunks) == "Controlled SSE answer."

    async def run():
        result = await model.ainvoke(
            "Controlled async", config=tracing_config("provider_async")
        )
        assert result.content == "Controlled HTTP answer."

    asyncio.run(run())
    try:
        model.invoke("FAIL_PROVIDER", config=tracing_config("provider_error"))
    except InternalServerError as error:
        assert isinstance(error, InternalServerError)
        print("Original provider error preserved.")
    else:
        raise AssertionError("Expected controlled provider error")


if __name__ == "__main__":
    main()
