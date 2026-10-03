"""Attach user, thread, and metadata attributes to Guardrails spans."""

from _shared import (
    example_attributes,
    local_guard,
    make_respan,
    result_summary,
    set_workflow_input,
)
from guardrails import Guard
from respan import workflow

WORKFLOW_NAME = "guardrails_propagated_attributes_workflow"


@workflow(name=WORKFLOW_NAME)
def propagated_attributes_workflow(guard: Guard, llm_output: str) -> dict:
    set_workflow_input({"llm_output": llm_output})
    return result_summary(
        guard.parse(
            llm_output=llm_output,
            num_reasks=0,
        )
    )


def run_propagated_attributes() -> None:
    respan, _ = make_respan("guardrails-propagated-attributes")
    guard = local_guard(Guard())
    llm_output = "Guardrails keeps structured outputs reliable."
    try:
        with example_attributes(
            "propagated-attributes",
            WORKFLOW_NAME,
            customer_identifier="example-user-guardrails",
            thread_identifier="guardrails-thread-001",
        ):
            result = propagated_attributes_workflow(
                guard=guard,
                llm_output=llm_output,
            )
        print("Workflow name:", WORKFLOW_NAME)
        print("Validation passed:", result["validation_passed"])
        print("Validated output:", result["validated_output"])
    finally:
        respan.shutdown()


if __name__ == "__main__":
    run_propagated_attributes()
