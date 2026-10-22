"""Validate a response, retry once, and retain user completion hooks."""

from typing import Literal

from _respan_instructor import attributes, create_respan_instructor_client, workflow
from pydantic import BaseModel, Field


class SupportEscalation(BaseModel):
    customer: str
    priority: Literal["low", "medium", "high"]
    follow_up_hours: int = Field(gt=0)


@workflow(name="instructor_example_02_validation_hooks")
def classify(client):
    return client.create(
        response_model=SupportEscalation,
        max_retries=2,
        messages=[{"role": "user", "content": "ACME needs a same-day response."}],
    )


def main():
    tracing, client = create_respan_instructor_client(
        app_name="instructor-validation-hooks",
        payload={"customer": "ACME", "priority": "high", "follow_up_hours": 4},
        invalid_attempts=1,
        invalid_field="follow_up_hours",
    )
    responses = []
    hooks = hasattr(client, "on")
    if hooks:
        client.on("completion:response", responses.append)
    try:
        with attributes("02_validation_hooks.py"):
            result = classify(client)
        print(result.model_dump())
        print({"completion_responses": len(responses), "native_hooks_available": hooks})
    finally:
        if hooks:
            client.off("completion:response", responses.append)
        tracing.shutdown()


if __name__ == "__main__":
    main()
