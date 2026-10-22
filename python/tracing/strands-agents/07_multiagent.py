"""Run two actual Strands agents in a directed graph."""

from _shared import create_gateway_model, create_respan, finish_respan, new_run_id
from respan import propagate_attributes, workflow
from strands import Agent
from strands.multiagent import GraphBuilder

WORKFLOW_NAME = "Strands Multiagent Example"


def main() -> None:
    run_id = new_run_id("graph")
    respan = create_respan("multiagent", run_id)
    try:
        builder = GraphBuilder()
        builder.add_node(
            Agent(
                name="researcher", model=create_gateway_model(), callback_handler=None
            ),
            "researcher",
        )
        builder.add_node(
            Agent(name="reviewer", model=create_gateway_model(), callback_handler=None),
            "reviewer",
        )
        builder.add_edge("researcher", "reviewer")
        builder.set_entry_point("researcher")
        graph = builder.build()

        @workflow(name=WORKFLOW_NAME)
        def run_workflow(prompt: str) -> dict[str, int]:
            result = graph(prompt)
            assert len(result.results) == 2
            return {"agents_completed": len(result.results)}

        with propagate_attributes(
            metadata={"run_id": run_id, "script": "07_multiagent.py"}
        ):
            print(run_workflow("Research and review one tracing tip."))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
