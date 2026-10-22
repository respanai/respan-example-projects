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
from helicone_helpers import HeliconeLogBuilder
from respan import workflow

EXAMPLE = "delayed-builder-context"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()
_PENDING_BUILDERS: list[HeliconeLogBuilder] = []


@workflow(name="helicone_delayed_builder_context")
def run(prompt: str) -> str:
    builder = logger.log_builder(
        {
            "model": "delayed-builder-model",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        },
        additional_headers={
            "Helicone-Session-Id": f"delayed-{RUN_MARKER}",
            "Helicone-Property-Phase": "created-inside-parent",
        },
    )
    _PENDING_BUILDERS.append(builder)
    return "builder-created"


async def main() -> None:
    try:
        with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
            result = run("Create now and send after the workflow context closes.")

        assert result == "builder-created"
        builder = _PENDING_BUILDERS.pop()

        builder.add_chunk(
            {
                "model": "delayed-builder-response-model",
                "choices": [{"delta": {"content": "Delayed child retained parent."}}],
                "usage": {
                    "prompt_tokens": 6,
                    "completion_tokens": 4,
                    "total_tokens": 10,
                },
            }
        )
        await builder.send_log()
        assert_local_logs(1)
        print_result(
            EXAMPLE,
            RUN_MARKER,
            {"delayed_send": True, "parent_context_snapshotted": True, "local_logs": 1},
        )
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
