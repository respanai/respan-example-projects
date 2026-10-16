"""Initial privacy opt-out and native errors without synthetic completions."""

import dspy
from _shared import FixtureLM, managed_example, traced_example


def main():
    with managed_example(
        app_name="dspy-08-privacy-errors",
        example_name="08_privacy_and_errors",
        include_content=False,
    ) as context:
        error = ValueError("controlled private provider failure")
        with traced_example(context):
            assert (
                dspy.Tool(lambda value: value)(value="private payload")
                == "private payload"
            )
            try:
                FixtureLM([error])("private prompt")
            except ValueError as observed:
                assert observed is error
            else:
                raise AssertionError("Native failure was swallowed")
        print("Privacy and native error identity verified")


if __name__ == "__main__":
    main()
