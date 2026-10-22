import asyncio

from _pipeline import run
from _shared import attributes, create_respan, finish_respan, marker, print_result
from opentelemetry import context
from respan import workflow
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


async def main():
    run_id = marker()
    sdk = create_respan("private-pipeline", run_id, capture=False)

    @workflow(name="pipecat_private_pipeline")
    async def scenario(prompt):
        collector, _worker = await run(
            tool=True, messages=[{"role": "user", "content": prompt}]
        )
        return {"native_frames_preserved": bool(collector.frames)}

    try:
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        try:
            with attributes("private-pipeline", run_id):
                result = await scenario("PRIVATE_PIPECAT_PROMPT")
        finally:
            context.detach(token)
        print_result("private-pipeline", result, run_id)
    finally:
        finish_respan(sdk)


if __name__ == "__main__":
    asyncio.run(main())
