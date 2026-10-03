"""Capture validator pass, noop failure, and fixed output."""

from _shared import example_attributes, local_guard, make_respan, result_summary
from _validators import AcceptedText
from guardrails import Guard
from respan import workflow

WORKFLOW_NAME = "guardrails_validator_outcomes_workflow"


@workflow(name=WORKFLOW_NAME)
def run_example():
    outcomes = []
    for action, value, expected in (
        ("noop", "fixture accepted", True),
        ("noop", "fixture rejected", False),
        ("fix", "fixture rejected", True),
    ):
        result = (
            local_guard(Guard())
            .use(AcceptedText(on_fail=action))
            .validate(value, num_reasks=0)
        )
        assert result.validation_passed is expected
        outcomes.append(result_summary(result))
    return outcomes


if __name__ == "__main__":
    respan, _ = make_respan(WORKFLOW_NAME)
    try:
        with example_attributes("validator-outcomes", WORKFLOW_NAME):
            print(run_example())
    finally:
        respan.shutdown()
