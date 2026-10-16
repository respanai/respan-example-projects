"""Trace a controlled provider failure without a synthetic success response."""

from _fixture import build_fixture_llm
from _shared import create_respan, print_result, traced_example
from llama_index.core.llms import ChatMessage


def main() -> None:
    context = create_respan(
        app_name="llama-index-error", example_name="11_provider_error"
    )
    try:
        with traced_example(
            context,
            root_span_name=context.example_name,
            input_data={"request": "controlled provider failure"},
        ):
            build_fixture_llm(fail=True).chat(
                [ChatMessage(role="user", content="controlled error prompt")]
            )
    except Exception as error:  # noqa: BLE001 - the released provider exception type is checked
        assert type(error).__name__ == "APIConnectionError"
        print_result("Expected failure", type(error).__name__)
    else:
        raise AssertionError("Controlled provider failure did not occur")


if __name__ == "__main__":
    main()
