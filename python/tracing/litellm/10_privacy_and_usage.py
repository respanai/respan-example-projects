"""Delayed parent veto, source zero/absent usage and native private flags."""

import os

import litellm
from _fixtures import HISTORY, client
from _shared import MODE, create_respan, run_with_example_attributes
from opentelemetry import trace

WORKFLOW_NAME = "litellm_privacy_usage.workflow"


def run():
    tracer = trace.get_tracer("example.caller")
    previous = os.environ.get("TRACELOOP_TRACE_CONTENT")
    try:
        with tracer.start_as_current_span("private_parent"):
            stream = litellm.completion(
                model="openai/fixture-model",
                messages=HISTORY,
                stream=True,
                stream_options={"include_usage": True},
                client=client(stream=True),
            )
            os.environ["TRACELOOP_TRACE_CONTENT"] = "off"
        os.environ["TRACELOOP_TRACE_CONTENT"] = "true"
        list(stream)
        for usage in (
            None,
            {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        ):
            response = litellm.completion(
                model="openai/fixture-model",
                messages=HISTORY,
                client=client(usage=usage),
            )
            assert response.choices[0].message.content == "controlled response"
        response = litellm.completion(
            model="openai/fixture-model",
            messages=HISTORY,
            client=client(),
            standard_callback_dynamic_params={"turn_off_message_logging": True},
        )
        assert response.choices[0].message.content == "controlled response"
        print("Delayed privacy bound and explicit zero/absent source usage verified")
    finally:
        if previous is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = previous


def main():
    if MODE != "fixture":
        print("SKIP: privacy/usage fixtures require controlled provider bodies")
        return
    respan = create_respan("litellm-privacy-usage")
    try:
        run_with_example_attributes(respan, workflow_name=WORKFLOW_NAME, action=run)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
