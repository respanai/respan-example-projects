"""Workflow and task spans around an Agno agent run."""

from _shared import build_agent, create_respan, example_attributes, print_result
from respan import task, workflow


@task(name="draft_prompt")
def draft_prompt(topic: str) -> str:
    return f"Write a two-bullet operational checklist for {topic}."


@workflow(name="agno_03_tracing_workflow")
def run_checklist_workflow(topic: str) -> str:
    agent = build_agent(
        name="Checklist Agent",
        instructions="Return exactly two bullets.",
    )
    prompt = draft_prompt(topic=topic)
    result = agent.run(prompt)
    return str(result.content)


def tracing() -> None:
    respan, _ = create_respan(app_name="agno-03-tracing")
    try:
        with example_attributes(respan, "agno_03_tracing_workflow"):
            output = run_checklist_workflow(topic="reviewing an SDK integration")
    finally:
        respan.shutdown()
    print_result("Workflow output", output)


if __name__ == "__main__":
    tracing()
