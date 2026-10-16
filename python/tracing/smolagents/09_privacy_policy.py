"""Exercise content opt-out and a policy veto during a model call."""

import os

from _shared import FixtureModel, build_respan, example_attributes, response
from opentelemetry import context
from respan import workflow
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY
from smolagents import Model

EXAMPLE_NAME = "privacy-policy"
WORKFLOW_NAME = "smolagents_privacy_policy_workflow"


@workflow(name=WORKFLOW_NAME)
def execute_privacy(label: str) -> str:
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    try:
        result = FixtureModel([response("private-smolagents-output")]).generate(
            [{"role": "user", "content": "private-smolagents-input"}]
        )
        assert result.content == "private-smolagents-output"
    finally:
        context.detach(token)

    class VetoModel(Model):
        def generate(self, messages, **kwargs):
            os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
            return response("private-smolagents-veto-output")

    previous = os.environ.get("TRACELOOP_TRACE_CONTENT")
    try:
        VetoModel(model_id="fixture-veto").generate(
            [{"role": "user", "content": "private-smolagents-veto-input"}]
        )
    finally:
        if previous is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = previous
    return "privacy fixtures completed"


def main():
    respan = build_respan(EXAMPLE_NAME, WORKFLOW_NAME)
    try:
        with example_attributes(EXAMPLE_NAME, WORKFLOW_NAME):
            print(execute_privacy("Verify content policy"))
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
