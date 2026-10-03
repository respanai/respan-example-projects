"""A native provider failure and a normally returned typed ToolFailure."""

from types import SimpleNamespace

from _fixtures import FixtureServer
from _shared import create_respan, run_with_attributes, shutdown_respan
from crewai import Agent
from crewai.tools import tool
from crewai.tools.tool_calling import ToolCalling
from crewai.tools.tool_failure import ToolFailure
from crewai.tools.tool_usage import ToolUsage
from openai import BadRequestError
from respan import workflow


@tool("fixture_failed_tool")
def fixture_failed_tool(city: str) -> str:
    """Report a controlled failure without raising from the tool."""
    return ToolFailure(
        message="controlled reported tool failure", code="fixture_failure"
    )


@workflow(name="crewai_08_failures")
def run_failures(scenario: str) -> dict:
    try:
        FixtureServer().llm().call("fixture-failure")
    except BadRequestError as exc:
        assert exc.status_code == 400
    agent = Agent(
        role="FailureAgent",
        goal="Run the fixture",
        backstory="Fixture",
        llm=FixtureServer().llm(),
        verbose=False,
    )
    usage = ToolUsage(
        tools_handler=None,
        tools=[fixture_failed_tool.to_structured_tool()],
        task=None,
        function_calling_llm=None,
        agent=agent,
        action=SimpleNamespace(
            tool="fixture_failed_tool", tool_input={"city": "Paris"}
        ),
    )
    result = usage.use(
        ToolCalling(tool_name="fixture_failed_tool", arguments={"city": "Paris"}),
        "fixture_failed_tool",
    )
    assert "controlled reported tool failure" in str(result)
    return {"scenario": scenario, "provider_error": True, "tool_failure": str(result)}


def main():
    context = create_respan(
        app_name="crewai-08-failures",
        example_name="08_failures",
        workflow_name="crewai_08_failures",
    )
    try:
        print(
            run_with_attributes(
                context, lambda: run_failures("typed-tool-and-provider-errors")
            )
        )
    finally:
        shutdown_respan(context)


if __name__ == "__main__":
    main()
