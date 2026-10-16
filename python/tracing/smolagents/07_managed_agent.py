"""Trace a managed agent under its parent agent step."""

from _shared import FixtureModel, build_respan, example_attributes, response, tool_call
from respan import workflow
from smolagents import ToolCallingAgent

EXAMPLE_NAME = "managed-agent"
WORKFLOW_NAME = "smolagents_managed_agent_workflow"


@workflow(name=WORKFLOW_NAME)
def execute_managed(task: str) -> str:
    child = ToolCallingAgent(
        tools=[],
        name="researcher",
        description="Return a controlled city fact",
        verbosity_level=0,
        model=FixtureModel(
            [
                response(
                    calls=[
                        tool_call(
                            "final_answer",
                            {"answer": "managed fact"},
                            "managed-child-final",
                        )
                    ]
                )
            ]
        ),
    )
    parent = ToolCallingAgent(
        tools=[],
        managed_agents=[child],
        verbosity_level=0,
        model=FixtureModel(
            [
                response(
                    calls=[
                        tool_call(
                            "researcher",
                            {"task": "Find the controlled city fact"},
                            "managed-request",
                        )
                    ]
                ),
                response(
                    calls=[
                        tool_call(
                            "final_answer",
                            {"answer": "managed fact"},
                            "managed-parent-final",
                        )
                    ]
                ),
            ]
        ),
    )
    result = parent.run(task)
    assert result == "managed fact"
    return result


def main():
    respan = build_respan(EXAMPLE_NAME, WORKFLOW_NAME)
    try:
        with example_attributes(EXAMPLE_NAME, WORKFLOW_NAME):
            print(execute_managed("Delegate a controlled fact lookup"))
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
