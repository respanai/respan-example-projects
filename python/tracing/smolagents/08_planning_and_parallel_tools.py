"""Trace planning and parallel tool calls with their real invocation IDs."""

from _shared import FixtureModel, build_respan, example_attributes, response, tool_call
from respan import workflow
from smolagents import ToolCallingAgent, tool

EXAMPLE_NAME = "planning-and-parallel-tools"
WORKFLOW_NAME = "smolagents_planning_parallel_tools_workflow"


@tool
def multiply(value: int) -> int:
    """Multiply by two.

    Args:
        value: Number to double.
    """
    return value * 2


@workflow(name=WORKFLOW_NAME)
def execute_parallel(task: str) -> str:
    model = FixtureModel(
        [
            response("Plan: double the two fixture values in parallel."),
            response(
                calls=[
                    tool_call("multiply", {"value": 2}, "parallel-2"),
                    tool_call("multiply", {"value": 3}, "parallel-3"),
                ]
            ),
            response(
                calls=[
                    tool_call("final_answer", {"answer": "4 and 6"}, "parallel-final")
                ]
            ),
        ]
    )
    agent = ToolCallingAgent(
        tools=[multiply], model=model, planning_interval=10, verbosity_level=0
    )
    result = agent.run(task)
    assert result == "4 and 6"
    return result


def main():
    respan = build_respan(EXAMPLE_NAME, WORKFLOW_NAME)
    try:
        with example_attributes(EXAMPLE_NAME, WORKFLOW_NAME):
            print(execute_parallel("Double 2 and 3 with the fixture tool"))
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
