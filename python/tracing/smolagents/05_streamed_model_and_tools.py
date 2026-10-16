"""Stream tool-call argument fragments through the released agent SDK."""

from _shared import FixtureModel, build_respan, example_attributes, response, tool_call
from respan import workflow
from smolagents import ToolCallingAgent, tool

EXAMPLE_NAME = "streamed-model-and-tools"
WORKFLOW_NAME = "smolagents_streamed_model_tools_workflow"


@tool
def echo_city(city: str) -> str:
    """Return a local city fact.

    Args:
        city: City to echo.
    """
    return f"{city}: controlled city fact"


@workflow(name=WORKFLOW_NAME)
def execute_streamed_model(label: str) -> str:
    model = FixtureModel(
        [
            response(
                calls=[tool_call("echo_city", {"city": "Paris"}, "stream-city-1")]
            ),
            response(
                calls=[
                    tool_call(
                        "final_answer",
                        {"answer": "Paris: controlled city fact"},
                        "stream-final-1",
                    )
                ]
            ),
        ]
    )
    agent = ToolCallingAgent(
        tools=[echo_city], model=model, stream_outputs=True, verbosity_level=0
    )
    result = ""
    for event in agent.run(label, stream=True):
        if type(event).__name__ == "FinalAnswerStep":
            result = event.output
    assert result == "Paris: controlled city fact"
    return result


def main():
    respan = build_respan(EXAMPLE_NAME, WORKFLOW_NAME)
    try:
        with example_attributes(EXAMPLE_NAME, WORKFLOW_NAME):
            print(execute_streamed_model("Use the city fixture"))
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
