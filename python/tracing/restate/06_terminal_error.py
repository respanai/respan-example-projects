"""The native terminal error and status survive instrumentation unchanged."""

import asyncio

import restate
from _shared import (
    create_respan,
    example_context,
    finish_respan,
    invoke_registered_handler,
)
from respan import workflow


@workflow(name="restate_terminal_error")
async def terminal_error(public_input: str):
    error = restate.TerminalError("controlled terminal failure", status_code=409)
    service = restate.Service("TerminalService")

    @service.handler(name="fail")
    async def fail(ctx, value):
        raise error

    try:
        await invoke_registered_handler(
            service,
            "fail",
            {"operation": public_input},
            invocation_id="terminal-error-1",
        )
    except restate.TerminalError as caught:
        assert caught is error and caught.status_code == 409
        return {"expected": "TerminalError", "status_code": caught.status_code}
    raise AssertionError("Expected native TerminalError")


async def main():
    respan = create_respan()
    try:
        with example_context("terminal_error"):
            print(await terminal_error("conflict"))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
