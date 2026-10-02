from __future__ import annotations

import asyncio

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

EXAMPLE = "builder-cancelled"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_builder_cancelled")
async def run(prompt: str) -> str:
    builder = logger.log_builder(
        {
            "model": "cancelled-builder-model",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
    )
    builder.set_error(asyncio.CancelledError("deterministic builder cancellation"))
    builder.was_cancelled = True
    await builder.send_log()
    return "expected-cancellation-logged"


async def main() -> None:
    try:
        with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
            outcome = await run("Cancel this deterministic builder request.")
        assert_local_logs(1)
        print_result(EXAMPLE, RUN_MARKER, {"outcome": outcome, "local_logs": 1})
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
