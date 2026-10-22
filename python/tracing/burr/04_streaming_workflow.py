"""Trace Burr streaming lifecycle events and content."""

from collections.abc import Generator

from _shared import create_respan, new_run_id, print_trace_lookup, workflow_context
from burr.core import ApplicationBuilder, State
from burr.core.action import streaming_action

WORKFLOW_NAME = "Burr Streaming Workflow"
EXAMPLE_NAME = "04_streaming_workflow"


@streaming_action(reads=["prompt"], writes=["response"])
def stream_response(state: State) -> Generator[tuple[dict, State | None], None, None]:
    chunks = ["trace", " trees", " clearly"]
    for chunk in chunks:
        yield {"delta": chunk}, None
    response = "".join(chunks)
    yield {"response": response}, state.update(response=response)


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
            app_id=f"{run_id}:{EXAMPLE_NAME}", partition_key="user-stream"
        )
        .with_actions(stream_response)
        .with_entrypoint("stream_response")
        .with_state(prompt="Return a deterministic streaming response")
        .build()
    )
    try:
        with workflow_context(
            respan,
            workflow_name=WORKFLOW_NAME,
            run_id=run_id,
            example_name=EXAMPLE_NAME,
        ):
            _, stream = app.stream_result(halt_after=["stream_response"])
            chunks = [item["delta"] for item in stream]
            result, state = stream.get()
        assert "".join(chunks) == "trace trees clearly"
        assert result["response"] == state["response"]
        print(f"Stream response: {state['response']}")
        print_trace_lookup(workflow_name=WORKFLOW_NAME, run_id=run_id)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
