"""Basic Braintrust workflow traced by Respan.

Run:
    python 01_basic_workflow.py
"""

from __future__ import annotations

from _shared import (
    create_braintrust_logger,
    create_respan,
    flush_and_shutdown,
    new_run_id,
    print_trace_lookup,
    workflow_context,
)

WORKFLOW_NAME = "Braintrust Basic Workflow"
EXAMPLE_NAME = "01_basic_workflow"


def run_basic_workflow() -> str:
    run_id = new_run_id(EXAMPLE_NAME)
    respan = create_respan(
        workflow_name=WORKFLOW_NAME,
        run_id=run_id,
        example_name=EXAMPLE_NAME,
    )
    logger = create_braintrust_logger(workflow_name=WORKFLOW_NAME)

    with (
        workflow_context(
            respan,
            workflow_name=WORKFLOW_NAME,
            run_id=run_id,
            example_name=EXAMPLE_NAME,
        ),
        logger.start_span(name=f"{WORKFLOW_NAME}.workflow", type="eval") as root,
    ):
        with root.start_span(name="draft_answer", type="llm") as span:
            span.log(
                input=[
                    {
                        "role": "user",
                        "content": "Summarize why Braintrust traces are useful.",
                    }
                ],
                output={
                    "role": "assistant",
                    "content": "They capture evaluations, prompts, outputs, and scores in one trace.",
                },
                metadata={"model": "gpt-4o-mini", "workflow_name": WORKFLOW_NAME},
                metrics={"prompt_tokens": 12, "completion_tokens": 14},
                scores={"helpfulness": 0.93},
            )

        root.log(
            input={"question": "Braintrust trace value"},
            output={"answer_ready": True},
            metadata={"workflow_name": WORKFLOW_NAME},
        )

    flush_and_shutdown(respan, logger)
    print_trace_lookup(workflow_name=WORKFLOW_NAME, run_id=run_id)
    return run_id


if __name__ == "__main__":
    run_basic_workflow()
