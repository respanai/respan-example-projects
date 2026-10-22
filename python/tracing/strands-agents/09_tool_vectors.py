"""Capture complete vectors returned by a native Strands tool."""

from _shared import create_gateway_model, create_respan, finish_respan, new_run_id
from respan import propagate_attributes, workflow
from strands import Agent, tool

WORKFLOW_NAME = "Strands Tool Vectors Example"


@tool
def get_vectors(city: str) -> dict[str, list[float]]:
    """Return a controlled complete vector for the example city."""
    return {"vectors": [float(index) for index in range(4096)]}


def main() -> None:
    run_id = new_run_id("vectors")
    respan = create_respan("tool_vectors", run_id)
    try:
        agent = Agent(
            name=WORKFLOW_NAME,
            model=create_gateway_model(),
            tools=[get_vectors],
            callback_handler=None,
        )

        @workflow(name=WORKFLOW_NAME)
        def run_workflow(prompt: str) -> dict[str, str]:
            return {"answer": str(agent(prompt))}

        with propagate_attributes(
            metadata={"run_id": run_id, "script": "09_tool_vectors.py"}
        ):
            print(run_workflow("Use get_vectors for Seattle."))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
