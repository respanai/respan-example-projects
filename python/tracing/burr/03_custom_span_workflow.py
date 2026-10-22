"""Trace Burr custom spans and logged attributes."""

from _shared import create_respan, new_run_id, print_trace_lookup, workflow_context
from burr.core import ApplicationBuilder, State, action
from burr.visibility import TracerFactory

WORKFLOW_NAME = "Burr Custom Span Workflow"
EXAMPLE_NAME = "03_custom_span_workflow"


@action(reads=["payload"], writes=["normalized"])
def normalize_payload(state: State, __tracer: TracerFactory) -> State:
    with __tracer("normalize_text") as custom_span:
        normalized = state["payload"].strip().lower()
        custom_span.log_attributes(
            operation="lowercase",
            original_length=len(state["payload"]),
            normalized=normalized,
        )
    return state.update(normalized=normalized)


def main() -> None:
    run_id = new_run_id(EXAMPLE_NAME)
    respan = create_respan(
        workflow_name=WORKFLOW_NAME,
        run_id=run_id,
        example_name=EXAMPLE_NAME,
    )
    app = (
        ApplicationBuilder()
        .with_identifiers(
            app_id=f"{run_id}:{EXAMPLE_NAME}", partition_key="user-custom"
        )
        .with_actions(normalize_payload)
        .with_entrypoint("normalize_payload")
        .with_state(payload="  Respan Trace  ")
        .build()
    )
    try:
        with workflow_context(
            respan,
            workflow_name=WORKFLOW_NAME,
            run_id=run_id,
            example_name=EXAMPLE_NAME,
        ):
            _, _, state = app.run(halt_after=["normalize_payload"])
        assert state["normalized"] == "respan trace"
        print(f"Normalized: {state['normalized']}")
        print_trace_lookup(workflow_name=WORKFLOW_NAME, run_id=run_id)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
