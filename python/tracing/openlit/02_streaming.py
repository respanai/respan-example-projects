from __future__ import annotations

import asyncio

from _shared import (
    async_client,
    create_respan,
    example_scope,
    finish_respan,
    provider_config,
    sync_client,
    workflow,
)

SCENARIO = "chat-responses-streaming"


def run_workflow(config) -> dict[str, str]:
    client = sync_client(config)

    @workflow(name="openlit_chat_responses_streaming_workflow")
    def traced_workflow(
        chat_prompt: str,
        responses_prompt: str,
        early_prompt: str,
    ) -> dict[str, str]:
        stream = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": chat_prompt}],
            stream=True,
            stream_options={"include_usage": True},
        )
        try:
            chat_text = "".join(
                chunk.choices[0].delta.content or ""
                for chunk in stream
                if chunk.choices
            )
        finally:
            stream.close()

        early = client.responses.create(
            model=config.model,
            input=early_prompt,
            stream=True,
        )
        try:
            first_event = next(early).type
        finally:
            early.close()

        async def async_stream() -> str:
            async_openai = async_client(config)
            response_stream = None
            try:
                response_stream = await async_openai.responses.create(
                    model=config.model,
                    input=responses_prompt,
                    stream=True,
                )
                parts: list[str] = []
                async for event in response_stream:
                    if event.type == "response.output_text.delta":
                        parts.append(event.delta)
                return "".join(parts)
            finally:
                if response_stream is not None:
                    await response_stream.close()
                await async_openai.close()

        return {
            "chat": chat_text,
            "responses": asyncio.run(async_stream()),
            "early_event": first_event,
        }

    try:
        return traced_workflow(
            chat_prompt="Stream a bounded reply.",
            responses_prompt="Stream a bounded Responses reply.",
            early_prompt="Close this Responses stream after the first event.",
        )
    finally:
        client.close()


def main() -> None:
    respan = create_respan(SCENARIO)
    try:
        with provider_config() as config, example_scope(SCENARIO):
            result = run_workflow(config)
            print(f"{SCENARIO}: {result}", flush=True)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
