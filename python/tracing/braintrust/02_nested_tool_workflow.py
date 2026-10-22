"""Nested Braintrust workflow with task, tool, and chat spans.

Run:
    python 02_nested_tool_workflow.py
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

WORKFLOW_NAME = "Braintrust Nested Tool Workflow"
EXAMPLE_NAME = "02_nested_tool_workflow"


def run_nested_tool_workflow() -> str:
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
        with root.start_span(name="prepare_context", type="task") as task:
            task.log(
                input={"topic": "support escalation"},
                output={"policy": "refund within 30 days"},
                metadata={"workflow_name": WORKFLOW_NAME},
            )

        with root.start_span(name="lookup_policy", type="tool") as tool:
            tool.log(
                input={"policy_id": "refund-window"},
                output={"days": 30, "requires_receipt": True},
                metadata={"workflow_name": WORKFLOW_NAME},
            )

        with root.start_span(name="compose_response", type="chat") as chat:
            chat.log(
                input=[
                    {
                        "role": "user",
                        "content": "Can I get a refund after 21 days?",
                    }
                ],
                output="Yes. Refunds are available within 30 days when a receipt is present.",
                metadata={"model": "gpt-4o-mini", "workflow_name": WORKFLOW_NAME},
                metrics={"input_tokens": 15, "output_tokens": 16},
            )

        root.log(
            input={"case_id": "case-1024"},
            output={"decision": "eligible"},
            scores={"policy_match": 1.0},
            metadata={"workflow_name": WORKFLOW_NAME},
        )

    flush_and_shutdown(respan, logger)
    print_trace_lookup(workflow_name=WORKFLOW_NAME, run_id=run_id)
    return run_id


if __name__ == "__main__":
    run_nested_tool_workflow()
