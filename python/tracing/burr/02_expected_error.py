"""Trace a deterministic Burr action and application failure."""

from _shared import create_respan, new_run_id, print_trace_lookup, workflow_context
from burr.core import ApplicationBuilder, State, action

WORKFLOW_NAME = "Burr Expected Error Workflow"
EXAMPLE_NAME = "02_expected_error"
EXPECTED_MESSAGE = "deterministic Burr failure"


@action(reads=["count"], writes=["count"])
def fail_deterministically(state: State) -> State:
    raise RuntimeError(EXPECTED_MESSAGE)


def main() -> None:
    run_id = new_run_id(EXAMPLE_NAME)
    respan = create_respan(
        workflow_name=WORKFLOW_NAME,
        run_id=run_id,
        example_name=EXAMPLE_NAME,
    )
    app = (
        ApplicationBuilder()
        .with_identifiers(app_id=f"{run_id}:{EXAMPLE_NAME}", partition_key="user-error")
        .with_actions(fail_deterministically)
        .with_entrypoint("fail_deterministically")
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
            try:
                app.run(halt_after=["fail_deterministically"])
            except RuntimeError as exc:
                assert str(exc) == EXPECTED_MESSAGE
            else:
                raise AssertionError("The failing Burr action unexpectedly succeeded")
        print(f"Observed expected error: {EXPECTED_MESSAGE}")
        print_trace_lookup(workflow_name=WORKFLOW_NAME, run_id=run_id)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
