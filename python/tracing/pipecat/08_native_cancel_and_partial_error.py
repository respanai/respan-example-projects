import asyncio

from _pipeline import Service, run
from _shared import attributes, create_respan, finish_respan, marker, print_result
from respan import workflow


async def main():
    run_id = marker()
    sdk = create_respan("cancel-and-partial-error", run_id)

    @workflow(name="pipecat_cancel_and_partial_error")
    async def scenario():
        cancelled, _ = await run(service=Service(cancel=True))
        partial, _ = await run(service=Service(fail=True, partial=True))
        return {
            "native_cancel_frame_received": any(
                type(f).__name__ == "CancelFrame" for f in cancelled.frames
            ),
            "actual_partial_text_preserved": any(
                getattr(f, "text", None) == "Actual partial text."
                for f in partial.frames
            ),
            "native_error_frame_received": any(
                type(f).__name__ == "ErrorFrame" for f in partial.frames
            ),
        }

    try:
        with attributes("cancel-and-partial-error", run_id):
            result = await scenario()
        print_result("cancel-and-partial-error", result, run_id)
    finally:
        finish_respan(sdk)


if __name__ == "__main__":
    asyncio.run(main())
