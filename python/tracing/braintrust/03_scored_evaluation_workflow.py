"""Braintrust scored evaluation workflow traced by Respan.

Run:
    python 03_scored_evaluation_workflow.py
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

WORKFLOW_NAME = "Braintrust Scored Evaluation Workflow"
EXAMPLE_NAME = "03_scored_evaluation_workflow"


def run_scored_evaluation_workflow() -> str:
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
        with root.start_span(name="candidate_answer", type="llm") as answer:
            answer.log(
                input=[
                    {
                        "role": "system",
                        "content": "Return a concise answer.",
                    },
                    {
                        "role": "user",
                        "content": "What should an incident summary include?",
                    },
                ],
                output={
                    "role": "assistant",
                    "content": "Impact, timeline, root cause, mitigation, and follow-up owners.",
                },
                metadata={"model": "gpt-4o-mini", "workflow_name": WORKFLOW_NAME},
                metrics={"prompt_tokens": 18, "completion_tokens": 13},
            )

        with root.start_span(name="score_answer", type="score") as score:
            score.log(
                input={"rubric": "incident-summary-completeness"},
                output={"score": 0.96, "reason": "All required fields present."},
                scores={"completeness": 0.96, "brevity": 0.9},
                metrics={"latency_ms": 1250},
                tags=["evaluation", "release"],
                metadata={"workflow_name": WORKFLOW_NAME},
            )

        root.log(
            input={"dataset_row": "incident-summary-001"},
            output={"passed": True},
            scores={"overall": 0.94},
            tags=["evaluation", "release"],
            metadata={"workflow_name": WORKFLOW_NAME},
        )

    flush_and_shutdown(respan, logger)
    print_trace_lookup(workflow_name=WORKFLOW_NAME, run_id=run_id)
    return run_id


if __name__ == "__main__":
    run_scored_evaluation_workflow()
