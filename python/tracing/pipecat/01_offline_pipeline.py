import asyncio

from _pipeline import run
from _shared import attributes, create_respan, finish_respan, marker, print_result
from respan import workflow


async def main():
    run_id = marker()
    sdk = create_respan("native-pipeline", run_id)

    @workflow(name="pipecat_native_pipeline")
    async def scenario(prompt):
        collector, _worker = await run(messages=[{"role": "user", "content": prompt}])
        return {
            "text": "".join(
                f.text for f in collector.frames if type(f).__name__ == "LLMTextFrame"
            )
        }

    try:
        with attributes("native-pipeline", run_id):
            result = await scenario("Trace the native Pipecat frame pipeline.")
        print_result("native-pipeline", result, run_id)
    finally:
        finish_respan(sdk)


if __name__ == "__main__":
    asyncio.run(main())
