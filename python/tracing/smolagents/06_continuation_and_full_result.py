"""Preserve native RunResult objects and conversation continuation."""

from _shared import FixtureModel, build_respan, example_attributes, response, tool_call
from respan import workflow
from smolagents import ToolCallingAgent
from smolagents.agents import RunResult

EXAMPLE_NAME = "continuation-and-full-result"
WORKFLOW_NAME = "smolagents_continuation_full_result_workflow"


@workflow(name=WORKFLOW_NAME)
def execute_continuation(first_task: str) -> dict:
    model = FixtureModel(
        [
            response(
                calls=[
                    tool_call("final_answer", {"answer": "first result"}, "continue-1")
                ]
            ),
            response(
                calls=[
                    tool_call("final_answer", {"answer": "second result"}, "continue-2")
                ]
            ),
        ]
    )
    agent = ToolCallingAgent(
        tools=[], model=model, return_full_result=True, verbosity_level=0
    )
    first = agent.run(first_task)
    before = len(agent.memory.steps)
    second = agent.run("Continue the prior task", reset=False)
    assert isinstance(first, RunResult) and isinstance(second, RunResult)
    assert len(agent.memory.steps) > before
    assert first.output == "first result" and second.output == "second result"
    return {"first": first.output, "second": second.output, "state": second.state}


def main():
    respan = build_respan(EXAMPLE_NAME, WORKFLOW_NAME)
    try:
        with example_attributes(EXAMPLE_NAME, WORKFLOW_NAME):
            print(execute_continuation("Start the continuation fixture"))
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
