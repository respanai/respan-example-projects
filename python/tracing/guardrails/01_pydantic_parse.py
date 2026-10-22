"""Validate known LLM output against a Pydantic schema."""

from typing import Literal

from _shared import (
    example_attributes,
    local_guard,
    make_respan,
    result_summary,
    set_workflow_input,
)
from guardrails import Guard
from pydantic import BaseModel, Field
from respan import workflow

WORKFLOW_NAME = "guardrails_pydantic_parse_workflow"


class SupportTicket(BaseModel):
    issue: str = Field(description="Short customer issue summary")
    urgency: Literal["low", "medium", "high"] = Field(description="Ticket urgency")


@workflow(name=WORKFLOW_NAME)
def pydantic_parse_workflow(guard: Guard, llm_output: str) -> dict:
    set_workflow_input({"llm_output": llm_output})
    return result_summary(
        guard.parse(
            llm_output=llm_output,
            num_reasks=0,
        )
    )


def run_pydantic_parse() -> None:
    respan, _ = make_respan("guardrails-pydantic-parse")
    guard = local_guard(Guard.for_pydantic(output_class=SupportTicket))
    llm_output = '{"issue": "Shipment arrived late", "urgency": "high"}'
    try:
        with example_attributes("pydantic-parse", WORKFLOW_NAME):
            result = pydantic_parse_workflow(guard=guard, llm_output=llm_output)
        print("Workflow name:", WORKFLOW_NAME)
        print("Validation passed:", result["validation_passed"])
        print("Validated output:", result["validated_output"])
    finally:
        respan.shutdown()


if __name__ == "__main__":
    run_pydantic_parse()
