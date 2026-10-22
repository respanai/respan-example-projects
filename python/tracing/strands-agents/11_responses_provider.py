"""Run the released Strands OpenAI Responses provider against controlled SSE."""

from _shared import create_respan, finish_respan, new_run_id
from respan import propagate_attributes, workflow
from strands import Agent

WORKFLOW_NAME = "Strands Responses Provider Example"


def main() -> None:
    try:
        from strands.models.openai_responses import OpenAIResponsesModel  # noqa: F401
    except ImportError:
        print({"skipped": "Responses provider unavailable in installed Strands"})
        return
    from _fixture import create_fixture_responses_model

    run_id = new_run_id("responses")
    respan = create_respan("responses_provider", run_id)
    try:
        agent = Agent(
            name=WORKFLOW_NAME,
            model=create_fixture_responses_model(),
            callback_handler=None,
        )

        @workflow(name=WORKFLOW_NAME)
        def run_workflow(prompt: str) -> dict[str, str]:
            answer = str(agent(prompt))
            assert "Responses fixture answer" in answer
            return {"answer": answer}

        with propagate_attributes(
            metadata={"run_id": run_id, "script": "11_responses_provider.py"}
        ):
            print(run_workflow("Use the Responses fixture."))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
