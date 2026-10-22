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

EXAMPLE = "builder-response"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_builder_response")
async def run(prompt: str) -> str:
    builder = logger.log_builder(
        {
            "model": "builder-initial-model",
            "messages": [{"role": "user", "content": prompt}],
        },
        additional_headers={"Helicone-Property-Mode": "non-streaming"},
    )
    builder.add_model("builder-request-model")
    response = {
        "model": "builder-response-model",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Helicone builder response recorded.",
                }
            }
        ],
        "usage": {
            "prompt_tokens": 5,
            "completion_tokens": 4,
            "total_tokens": 9,
        },
    }
    builder.add_response(response)
    await builder.send_log()
    return response["choices"][0]["message"]["content"]


async def main() -> None:
    try:
        with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
            output = await run("Record one non-streaming builder response.")
        assert_local_logs(1)
        print_result(EXAMPLE, RUN_MARKER, {"output": output, "local_logs": 1})
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
