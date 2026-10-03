"""CrewAI example that attaches user, thread, and metadata attributes."""

from _shared import (
    build_llm,
    create_respan,
    print_result,
    result_text,
    run_with_attributes,
    shutdown_respan,
)

WORKFLOW_NAME = "crewai_03_attributes"


def run_attribute_crew(context) -> str:
    from crewai import Agent, Crew, Process, Task

    llm = build_llm(context.settings)
    analyst = Agent(
        role="Support Analyst",
        goal="Classify a support request and suggest the next action",
        backstory="You help support teams triage incoming tickets quickly.",
        llm=llm,
        verbose=False,
    )
    task = Task(
        name="Triage support request",
        description=(
            "A customer says: 'The dashboard loads slowly after I add a new "
            "integration.' Classify the issue and suggest one next action."
        ),
        expected_output="A category and one recommended next action.",
        agent=analyst,
    )
    crew = Crew(
        name=WORKFLOW_NAME,
        agents=[analyst],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
    return result_text(crew.kickoff())


def main() -> None:
    context = create_respan(
        app_name="crewai-03-attributes",
        example_name="03_attributes",
        workflow_name=WORKFLOW_NAME,
        metadata={"scenario": "support_triage"},
    )
    try:
        output = run_with_attributes(context, lambda: run_attribute_crew(context))
        print_result("Crew output", output)
        print_result("Workflow name", WORKFLOW_NAME)
        print_result("Example run id", context.run_id)
    finally:
        shutdown_respan(context)


if __name__ == "__main__":
    main()
