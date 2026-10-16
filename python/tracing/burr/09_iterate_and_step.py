"""Preserve Burr's native iteration and single-step execution."""

import inspect

from _shared import create_respan, new_run_id, print_trace_lookup
from burr.core import ApplicationBuilder, State, action

EXAMPLE_NAME = "09_iterate_and_step"
WORKFLOW_NAME = "Burr Iterate and Step Workflow"


@action(reads=["value"], writes=["value"])
def increment(state: State) -> State:
    return state.update(value=state["value"] + 1)


def app(run_id: str, suffix: str):
    return (
        ApplicationBuilder()
        .with_actions(increment)
        .with_entrypoint("increment")
        .with_identifiers(
            app_id=f"{run_id}:{EXAMPLE_NAME}:{suffix}",
            partition_key="controlled-iterate-thread",
        )
        .with_state(value=1)
        .build()
    )


def main() -> None:
    run_id = new_run_id(EXAMPLE_NAME)
    runtime = create_respan(
        workflow_name=WORKFLOW_NAME, run_id=run_id, example_name=EXAMPLE_NAME
    )
    try:
        iterator = app(run_id, "iterate").iterate(halt_after=["increment"])
        assert inspect.isgenerator(iterator)
        outputs = list(iterator)
        assert outputs[0][2]["value"] == 2
        assert app(run_id, "step").step()[2]["value"] == 2
        print_trace_lookup(workflow_name=WORKFLOW_NAME, run_id=run_id)
    finally:
        runtime.shutdown()


if __name__ == "__main__":
    main()
