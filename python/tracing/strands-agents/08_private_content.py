"""Run a real agent while content capture is disabled."""

import os

from _shared import create_gateway_model, create_respan, finish_respan, new_run_id
from respan import propagate_attributes, workflow
from strands import Agent

WORKFLOW_NAME = "Strands Private Content Example"


def main() -> None:
    run_id = new_run_id("private")
    respan = create_respan("private_content", run_id)
    previous = os.environ.get("TRACELOOP_TRACE_CONTENT")
    try:
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
        agent = Agent(
            name=WORKFLOW_NAME, model=create_gateway_model(), callback_handler=None
        )

        @workflow(name=WORKFLOW_NAME)
        def run_workflow(prompt: str) -> dict[str, str]:
            return {"answer": str(agent(prompt))}

        with propagate_attributes(
            metadata={"run_id": run_id, "script": "08_private_content.py"}
        ):
            result = run_workflow("private-fixture-prompt")
        print({"completed": bool(result)})
    finally:
        if previous is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = previous
        finish_respan(respan)


if __name__ == "__main__":
    main()
