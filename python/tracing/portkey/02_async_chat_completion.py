from __future__ import annotations

import asyncio

from _shared import (
    example_attributes,
    execution_id,
    finish_respan,
    make_async_client,
    make_respan,
    marker,
    model_name,
    print_result,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "async-chat-completion"


@workflow(name=workflow_name(EXAMPLE_NAME))
async def trace_async_chat(prompt: str) -> dict[str, str]:
    client = make_async_client()
    try:
        response = await client.chat.completions.create(
            model=model_name(), messages=[{"role": "user", "content": prompt}]
        )
        stream = await client.chat.completions.create(
            model=model_name(),
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        content = "".join(
            [
                chunk.choices[0].delta.content or ""
                async for chunk in stream
                if chunk.choices
            ]
        )
        embedding = await client.embeddings.create(
            model="fixture-embedding", input=prompt
        )
        result = await client.responses.create(model="fixture-responses", input=prompt)
        return {
            "response": response.choices[0].message.content or "",
            "stream": content,
            "embedding_dimensions": len(embedding.data[0].embedding),
            "response_call_id": result.output[1].call_id,
        }
    finally:
        await client.close()


async def main() -> None:
    run_marker = marker()
    execution = execution_id()
    respan = make_respan(EXAMPLE_NAME, run_marker)
    try:
        with example_attributes(
            EXAMPLE_NAME, run_marker, execution, mode="deterministic"
        ):
            result = await trace_async_chat("Explain tracing in one concise sentence.")
        print_result(EXAMPLE_NAME, run_marker, result)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
