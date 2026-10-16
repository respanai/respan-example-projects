"""Keep the SDK's Future and its original asynchronous upload failure."""

import requests
from _fixture import SPACE_ID
from _shared import example
from arize.ml.types import Environments, ModelTypes


def main():
    try:
        with example("09_native_future_error", failure=True) as client:
            future = client.ml.log_stream(
                space_id=SPACE_ID,
                model_name="fixture-regression",
                model_type=ModelTypes.REGRESSION,
                environment=Environments.PRODUCTION,
                prediction_label=1.0,
            )
            future.result(timeout=5)
    except requests.ConnectionError as error:
        assert future.exception() is error
        print("Expected native Future error: " + type(error).__name__)
    else:
        raise AssertionError("Controlled Future failure was not raised")


if __name__ == "__main__":
    main()
