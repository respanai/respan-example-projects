"""Record native ERROR spans while preserving the raised validation exception."""

from _shared import example_attributes, local_guard, make_respan
from _validators import AcceptedText
from guardrails import Guard
from guardrails.errors import ValidationError
from respan import workflow

WORKFLOW_NAME = "guardrails_controlled_error_workflow"


@workflow(name=WORKFLOW_NAME)
def run_example():
    try:
        local_guard(Guard()).use(AcceptedText(on_fail="exception")).validate(
            "fixture rejected", num_reasks=0
        )
    except ValidationError as exc:
        assert "Expected fixture accepted" in str(exc)
        return {"expected_error": type(exc).__name__}
    raise AssertionError("Expected the local validator to reject its fixture")


if __name__ == "__main__":
    respan, _ = make_respan(WORKFLOW_NAME)
    try:
        with example_attributes("controlled-error", WORKFLOW_NAME):
            print(run_example())
    finally:
        respan.shutdown()
