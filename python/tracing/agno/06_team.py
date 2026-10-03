"""Trace an Agno team run."""

from _shared import (
    build_agent,
    build_model,
    create_respan,
    example_attributes,
    print_result,
)
from agno.models.openai import OpenAIChat
from agno.team import Team
from respan import workflow


class DelegatingOpenAIChat(OpenAIChat):
    """Force the first team turn to delegate, then let it summarize."""

    def invoke(self, *args, **kwargs):
        messages = kwargs.get("messages", [])
        has_delegation_result = any(
            getattr(message, "role", None) == "tool"
            and getattr(message, "tool_name", None) == "delegate_task_to_members"
            for message in messages
        )
        kwargs["tool_choice"] = (
            "none"
            if has_delegation_result
            else {
                "type": "function",
                "function": {"name": "delegate_task_to_members"},
            }
        )
        return super().invoke(*args, **kwargs)


@workflow(name="agno_06_team")
def run_team() -> str:
    researcher = build_agent(
        name="Researcher",
        instructions="Find the most relevant operational facts.",
    )
    writer = build_agent(
        name="Writer",
        instructions="Turn operational facts into concise prose.",
    )
    team_agent = Team(
        name="Tracing Team",
        model=build_model(DelegatingOpenAIChat),
        members=[researcher, writer],
        telemetry=False,
        delegate_to_all_members=True,
        instructions=(
            "Delegate this task to every member. The Researcher supplies facts, "
            "then the Writer turns those facts into the final concise paragraph."
        ),
    )

    result = team_agent.run("Explain why tool spans are useful in one paragraph.")
    return str(result.content)


def team() -> None:
    respan, _ = create_respan(app_name="agno-06-team")
    try:
        with example_attributes(respan, "agno_06_team"):
            output = run_team()
    finally:
        respan.shutdown()
    print_result("Team output", output)


if __name__ == "__main__":
    team()
