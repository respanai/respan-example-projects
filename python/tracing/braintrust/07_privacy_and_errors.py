"""Late parent veto, source zero usage, and actual native exception identity."""

import os

from _shared import (
    create_braintrust_logger,
    create_respan,
    flush_and_shutdown,
    new_run_id,
    workflow_context,
)

NAME = "07_privacy_and_errors"
WORKFLOW = "Braintrust Privacy"


def main():
    marker = new_run_id(NAME)
    respan = create_respan(workflow_name=WORKFLOW, run_id=marker, example_name=NAME)
    logger = create_braintrust_logger(workflow_name=WORKFLOW)
    previous = os.environ.get("TRACELOOP_TRACE_CONTENT")
    try:
        with workflow_context(
            respan, workflow_name=WORKFLOW, run_id=marker, example_name=NAME
        ):
            with logger.start_span(name="private_parent", type="eval") as root:
                with root.start_span(name="private_model", type="llm") as child:
                    child.log(
                        input="private prompt",
                        output="private output",
                        metadata={
                            "model": "fixture-zero",
                            "provider": "openai",
                            "usage": {
                                "input_tokens": 0,
                                "output_tokens": 0,
                                "total_tokens": 0,
                            },
                        },
                    )
                os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
            os.environ["TRACELOOP_TRACE_CONTENT"] = "true"
            error = ValueError("controlled native failure")
            try:
                with logger.start_span(name="failed_model", type="llm") as span:
                    span.log(
                        input="controlled question", metadata={"model": "fixture-error"}
                    )
                    raise error
            except ValueError as seen:
                assert seen is error
        print("Private payload veto, zero usage and native error identity verified")
    finally:
        if previous is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = previous
        flush_and_shutdown(respan, logger)


if __name__ == "__main__":
    main()
