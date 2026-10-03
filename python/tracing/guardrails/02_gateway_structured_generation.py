"""Generate structured output with a local LiteLLM fixture (live gateway opt-in)."""

import os
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

WORKFLOW_NAME = "guardrails_gateway_structured_generation_workflow"


class ProductRecommendation(BaseModel):
    product: str = Field(description="Recommended product name")
    reason: str = Field(description="One sentence explaining the recommendation")
    confidence: Literal["low", "medium", "high"] = Field(
        description="Confidence in the recommendation"
    )


@workflow(name=WORKFLOW_NAME)
def gateway_structured_generation_workflow(
    guard: Guard, model: str, prompt: str
) -> dict:
    set_workflow_input({"model": model, "prompt": prompt})
    return result_summary(
        guard(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            num_reasks=1,
            **(
                {}
                if os.getenv("RESPAN_GUARDRAILS_LIVE") == "1"
                else {
                    "mock_response": '{"product":"Fixture backpack","reason":"Durable fixture material","confidence":"high"}'
                }
            ),
        )
    )


def run_gateway_structured_generation() -> None:
    respan, model = make_respan("guardrails-gateway-structured-generation")
    if os.getenv("RESPAN_GUARDRAILS_LIVE") == "1":
        os.environ["OPENAI_API_KEY"] = os.environ["RESPAN_API_KEY"]
        os.environ["OPENAI_API_BASE"] = os.getenv(
            "RESPAN_BASE_URL", "https://api.respan.ai/api"
        )
    guard = local_guard(Guard.for_pydantic(output_class=ProductRecommendation))
    prompt = (
        "Recommend one durable backpack for a weekend hiking trip. "
        "Return JSON with product, reason, and confidence."
    )
    try:
        with example_attributes("gateway-structured-generation", WORKFLOW_NAME):
            result = gateway_structured_generation_workflow(
                guard=guard,
                model=model,
                prompt=prompt,
            )
        assert result["validation_passed"]
        print("Workflow name:", WORKFLOW_NAME)
        print("Raw output:", result["raw_llm_output"])
        print("Validation passed:", result["validation_passed"])
        print("Validated output:", result["validated_output"])
    finally:
        respan.shutdown()


if __name__ == "__main__":
    run_gateway_structured_generation()
