"""Run an actual two-step standalone Workflows execution."""

import asyncio

from _shared import create_respan, print_result, traced_example
from workflows import Workflow, step
from workflows.events import Event, StartEvent, StopEvent


class Draft(Event):
    text: str


class TraceTipWorkflow(Workflow):
    @step
    async def draft(self, ev: StartEvent) -> Draft:
        return Draft(text=f"Inspect the {ev.topic} span")

    @step
    async def finish(self, ev: Draft) -> StopEvent:
        return StopEvent(result=ev.text)


async def main() -> None:
    context = create_respan(
        app_name="llama-index-native-workflow", example_name="08_native_workflow"
    )
    with traced_example(
        context, root_span_name=context.example_name, input_data={"topic": "failed"}
    ) as root:
        result = await TraceTipWorkflow().run(topic="failed")
        assert result == "Inspect the failed span"
        root.set_output({"result": result})
    print_result("Native workflow", result)


if __name__ == "__main__":
    asyncio.run(main())
