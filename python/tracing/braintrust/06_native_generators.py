"""Native traced functions and detached sync/async generator advances."""

import asyncio

import braintrust
from _shared import (
    create_braintrust_logger,
    create_respan,
    flush_and_shutdown,
    new_run_id,
    workflow_context,
)
from opentelemetry import trace

NAME = "06_native_generators"
WORKFLOW = "Braintrust Generators"


@braintrust.traced(name="native_sync")
def calculate(value):
    return {"value": value}


@braintrust.traced(name="native_generator")
def generate():
    yield "first"
    yield "second"


@braintrust.traced(name="native_async_generator")
async def agenerate():
    yield "async-first"
    yield "async-second"


async def main():
    marker = new_run_id(NAME)
    respan = create_respan(workflow_name=WORKFLOW, run_id=marker, example_name=NAME)
    logger = create_braintrust_logger(workflow_name=WORKFLOW)
    try:
        with (
            workflow_context(
                respan, workflow_name=WORKFLOW, run_id=marker, example_name=NAME
            ),
            logger.start_span(name=WORKFLOW, type="eval"),
        ):
            assert calculate(3) == {"value": 3}
            before = trace.get_current_span()
            iterator = generate()
            assert next(iterator) == "first"
            assert trace.get_current_span() is before
            assert iterator.send(None) == "second"
            iterator.close()
            iterator = agenerate()
            assert await iterator.__anext__() == "async-first"
            assert trace.get_current_span() is before
            assert await iterator.asend(None) == "async-second"
            await iterator.aclose()
        print("Native function/generator results and caller context verified")
    finally:
        flush_and_shutdown(respan, logger)


if __name__ == "__main__":
    asyncio.run(main())
