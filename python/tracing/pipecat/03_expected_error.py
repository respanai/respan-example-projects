import asyncio

from _pipeline import run
from _shared import attributes, create_respan, finish_respan, marker, print_result
from respan import workflow


async def main():
    run_id = marker()
    sdk = create_respan("native-error", run_id)

    @workflow(name="pipecat_native_error")
    async def scenario():
        collector, _worker = await run(fail=True)
        errors = [f for f in collector.frames if type(f).__name__ == "ErrorFrame"]
        return {
            "actual_error_type": type(errors[0].exception).__name__,
            "native_error_frame_received": True,
        }

    try:
        with attributes("native-error", run_id):
            result = await scenario()
        print_result("native-error", result, run_id)
    finally:
        finish_respan(sdk)


if __name__ == "__main__":
    asyncio.run(main())
