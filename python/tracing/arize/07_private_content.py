"""Retain native results while adapter content capture is disabled."""

import os

from _fixture import SPACE_ID
from _shared import example, print_result
from arize.ml.types import Environments, ModelTypes


def main():
    previous = os.environ.get("TRACELOOP_TRACE_CONTENT")
    try:
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
        with example("07_private_content") as client:
            result = client.datasets.list(name="private-fixture-input")
            print_result("Private native result", result)
            future = client.ml.log_stream(
                space_id=SPACE_ID,
                model_name="fixture-regression",
                model_type=ModelTypes.REGRESSION,
                environment=Environments.PRODUCTION,
                prediction_label=1.0,
                features={"private": "private-fixture-feature"},
            )
            assert future.result(timeout=5).status_code == 202
    finally:
        if previous is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = previous


if __name__ == "__main__":
    main()
