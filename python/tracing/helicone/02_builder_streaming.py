from __future__ import annotations

from _shared import (
    assert_local_logs,
    example_attributes,
    execution_id,
    finish_respan,
    make_logger,
    make_respan,
    marker,
    print_result,
)
from respan import workflow

EXAMPLE = "builder-streaming"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_builder_streaming")
async def run(prompt: str) -> str:
    builder = logger.log_builder(
        {
            "model": "local-helicone-stream",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        },
        additional_headers={"Helicone-Property-Mode": "streaming"},
    )
    chunks = ["Helicone ", "builder ", "streamed."]
    for index, text in enumerate(chunks):
        builder.add_chunk(
            {
                "model": "local-helicone-stream",
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "role": "assistant" if index == 0 else None,
                            "content": text,
                        },
                    }
                ],
                "usage": (
                    {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}
                    if index == len(chunks) - 1
                    else None
                ),
            }
        )
    await builder.send_log()
    return "".join(chunks)


async def main() -> None:
    try:
        with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
            output = await run("Return three streamed words.")
        assert_local_logs(1)
        print_result(EXAMPLE, RUN_MARKER, {"output": output, "local_logs": 1})
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
