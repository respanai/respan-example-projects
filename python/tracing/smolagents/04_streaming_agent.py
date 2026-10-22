"""Trace a streamed smolagents ToolCallingAgent run."""

from _shared import build_model, build_respan, example_attributes
from respan import workflow
from smolagents import ToolCallingAgent

EXAMPLE_NAME = "streaming-agent"
WORKFLOW_NAME = "smolagents_streaming_agent_workflow"


@workflow(name=WORKFLOW_NAME)
def execute_streaming_agent(prompt: str) -> str:
    agent = ToolCallingAgent(
        tools=[], model=build_model("stream"), max_steps=2, verbosity_level=0
    )
    result = ""
    for chunk in agent.run(prompt, stream=True):
        value = getattr(chunk, "output", None)
        if isinstance(value, str):
            result = value
    print(result)
    return result


def main() -> None:
    respan = build_respan(EXAMPLE_NAME, WORKFLOW_NAME)
    try:
        with example_attributes(EXAMPLE_NAME, WORKFLOW_NAME):
            execute_streaming_agent("Return exactly: streamed smolagents tracing works")
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
