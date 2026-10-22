"""Trace a deterministic successful Burr state machine."""

from _shared import create_respan, new_run_id, print_trace_lookup, workflow_context
from burr.core import ApplicationBuilder, Result, State, action, default, expr

WORKFLOW_NAME = "Burr Counter Workflow"
EXAMPLE_NAME = "01_counter_workflow"


@action(reads=["count"], writes=["count"])
def increment(state: State) -> State:
    return state.update(count=state["count"] + 1)


def main() -> None:
    run_id = new_run_id(EXAMPLE_NAME)
    respan = create_respan(
        workflow_name=WORKFLOW_NAME,
        run_id=run_id,
        example_name=EXAMPLE_NAME,
    )
    result = Result("count").with_name("result")
    app = (
        ApplicationBuilder()
        .with_identifiers(app_id=f"{run_id}:{EXAMPLE_NAME}", partition_key="user-42")
        .with_actions(increment, result)
        .with_transitions(("increment", "increment", expr("count < 2")))
        .with_transitions(("increment", "result", default))
        .with_entrypoint("increment")
        .with_state(count=0)
        .build()
    )
    try:
        with workflow_context(
            respan,
            workflow_name=WORKFLOW_NAME,
            run_id=run_id,
            example_name=EXAMPLE_NAME,
        ):
            _, _, state = app.run(halt_after=["result"])
        assert state["count"] == 2
        print(f"Final count: {state['count']}")
        print_trace_lookup(workflow_name=WORKFLOW_NAME, run_id=run_id)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
