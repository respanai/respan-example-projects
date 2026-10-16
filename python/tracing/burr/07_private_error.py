"""Keep native error identity while suppressing payloads and error diagnostics."""

import json

from _shared import create_respan, new_run_id, print_trace_lookup
from burr.core import ApplicationBuilder, State, action
from burr.visibility import TracerFactory
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY

EXAMPLE_NAME = "07_private_error"
WORKFLOW_NAME = "Burr Private Error Workflow"
PRIVATE = "controlled-burr-private-content"
ERROR = RuntimeError(PRIVATE)


@action(reads=["payload"], writes=[])
def private_error(state: State, __tracer: TracerFactory) -> State:
    with __tracer("private_custom") as custom:
        custom.log_attributes(payload=state["payload"])
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        context.detach(token)
        raise ERROR


def main() -> None:
    run_id = new_run_id(EXAMPLE_NAME)
    runtime = create_respan(
        workflow_name=WORKFLOW_NAME, run_id=run_id, example_name=EXAMPLE_NAME
    )
    app = (
        ApplicationBuilder()
        .with_actions(private_error)
        .with_entrypoint("private_error")
        .with_identifiers(
            app_id=f"{run_id}:{EXAMPLE_NAME}", partition_key="controlled-private-thread"
        )
        .with_state(payload=PRIVATE)
        .build()
    )
    try:
        try:
            app.run(halt_after=["private_error"])
        except RuntimeError as exc:
            assert exc is ERROR
        else:
            raise AssertionError("Expected the controlled native Burr error")
        spans = runtime.memory.get_finished_spans()
        assert len(spans) == 3
        assert PRIVATE not in json.dumps(
            [
                {
                    "attributes": dict(s.attributes),
                    "events": [str(e) for e in s.events],
                    "description": s.status.description,
                }
                for s in spans
            ]
        )
        assert all(s.status.description is None and not s.events for s in spans)
        print_trace_lookup(workflow_name=WORKFLOW_NAME, run_id=run_id)
    finally:
        runtime.shutdown()


if __name__ == "__main__":
    main()
