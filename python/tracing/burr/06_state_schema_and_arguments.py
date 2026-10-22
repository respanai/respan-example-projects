"""Retain structured state, tool history, schemas, vectors, and native arguments."""

from _shared import create_respan, new_run_id, print_trace_lookup
from burr.core import ApplicationBuilder, State, action

EXAMPLE_NAME = "06_state_schema_and_arguments"
WORKFLOW_NAME = "Burr Structured State Workflow"
PAYLOAD = {
    "history": [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "controlled-call-1",
                    "function": {"name": "lookup", "arguments": '{"query":"fixture"}'},
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "controlled-call-1",
            "content": "fixture result",
        },
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "lookup",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        }
    ],
    "dense": [0.25, 0.5, 0.75],
    "sparse": {"indices": [2, 9], "values": [0.1, 0.9]},
}


@action(reads=["payload"], writes=["result"])
def preserve(state: State, arguments: dict) -> State:
    return state.update(result={"payload": state["payload"], "arguments": arguments})


def main() -> None:
    run_id = new_run_id(EXAMPLE_NAME)
    runtime = create_respan(
        workflow_name=WORKFLOW_NAME, run_id=run_id, example_name=EXAMPLE_NAME
    )
    arguments = {"query": "fixture", "call_id": "controlled-call-1"}
    app = (
        ApplicationBuilder()
        .with_actions(preserve)
        .with_entrypoint("preserve")
        .with_identifiers(
            app_id=f"{run_id}:{EXAMPLE_NAME}", partition_key="controlled-thread"
        )
        .with_state(payload=PAYLOAD)
        .build()
    )
    try:
        _, _, state = app.run(halt_after=["preserve"], inputs={"arguments": arguments})
        assert state["result"]["payload"] is PAYLOAD
        assert state["result"]["arguments"] is arguments
        print_trace_lookup(workflow_name=WORKFLOW_NAME, run_id=run_id)
    finally:
        runtime.shutdown()


if __name__ == "__main__":
    main()
