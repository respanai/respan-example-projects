"""Run Mirascope's OpenAI provider against the configured Respan gateway."""

from __future__ import annotations

from _shared import (
    close_model_provider,
    create_live_model,
    create_respan,
    finish_respan,
    live_example_enabled,
    workflow_attributes,
)
from mirascope import llm
from respan import workflow

WORKFLOW_NAME = "mirascope-live-gateway"


def create_runner(model: llm.Model):
    @workflow(name=WORKFLOW_NAME)
    def run_live_call(prompt: str) -> str:
        response = model.call(prompt)
        return response.text()

    return run_live_call


def main() -> None:
    if not live_example_enabled():
        print("skipped live gateway; set RESPAN_MIRASCOPE_RUN_LIVE=1 to enable")
        return

    respan = create_respan(WORKFLOW_NAME)
    model: llm.Model | None = None
    try:
        model = create_live_model()
        runner = create_runner(model)
        with respan.propagate_attributes(
            **workflow_attributes(WORKFLOW_NAME, "05_live_gateway.py")
        ):
            result = runner("Reply with exactly: Mirascope live tracing works.")
        print(result)
    finally:
        try:
            if model is not None:
                close_model_provider(model)
        finally:
            finish_respan(respan)


if __name__ == "__main__":
    main()
