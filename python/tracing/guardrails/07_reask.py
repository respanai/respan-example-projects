"""Repair schema-invalid output on a deterministic second LLM call."""

from _shared import example_attributes, local_guard, make_respan, result_summary
from guardrails import Guard
from pydantic import BaseModel
from respan import workflow

WORKFLOW_NAME = "guardrails_reask_workflow"


class Reply(BaseModel):
    answer: str
    priority: str


@workflow(name=WORKFLOW_NAME)
def run_example():
    responses = iter(
        [
            '{"answer":"Missing priority"}',
            '{"answer":"Repaired fixture","priority":"high"}',
        ]
    )

    def generate(*, messages, **kwargs):
        return next(responses)

    result = local_guard(Guard.for_pydantic(Reply))(
        llm_api=generate,
        messages=[{"role": "user", "content": "Return answer and priority"}],
        num_reasks=1,
    )
    assert result.validation_passed
    return result_summary(result)


if __name__ == "__main__":
    respan, _ = make_respan(WORKFLOW_NAME)
    try:
        with example_attributes("reask", WORKFLOW_NAME):
            print(run_example())
    finally:
        respan.shutdown()
