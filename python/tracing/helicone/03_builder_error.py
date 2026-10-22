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

EXAMPLE = "builder-error"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_builder_error")
async def run(trigger_prompt: str) -> str:
    builder = logger.new_builder(
        {
            "model": "local-helicone-error",
            "messages": [{"role": "user", "content": trigger_prompt}],
        }
    )
    builder.set_error(RuntimeError("deterministic Helicone builder failure"))
    await builder.send_log()
    return "expected-error-logged"


async def main() -> None:
    try:
        with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
            outcome = await run("Trigger the deterministic error path.")
        assert_local_logs(1)
        print_result(EXAMPLE, RUN_MARKER, {"outcome": outcome, "local_logs": 1})
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
