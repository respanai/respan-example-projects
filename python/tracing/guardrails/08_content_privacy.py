"""Keep guard/validator payloads absent when content capture is disabled."""

import os

os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
from _shared import example_attributes, local_guard, make_respan
from _validators import AcceptedText
from guardrails import Guard
from respan import workflow

WORKFLOW_NAME = "guardrails_privacy_workflow"


@workflow(name=WORKFLOW_NAME)
def run_example():
    result = (
        local_guard(Guard())
        .use(AcceptedText(on_fail="noop"))
        .validate(
            "private fixture sentinel",
            metadata={"note": "private fixture metadata"},
            num_reasks=0,
        )
    )
    assert not result.validation_passed
    return {"validation_passed": result.validation_passed}


if __name__ == "__main__":
    respan, _ = make_respan(WORKFLOW_NAME)
    try:
        with example_attributes("privacy", WORKFLOW_NAME):
            print(run_example())
    finally:
        respan.shutdown()
