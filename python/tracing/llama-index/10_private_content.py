"""Run released chat and embedding providers with content capture disabled."""

import os

from _shared import (
    build_embedding_model,
    build_llm,
    create_respan,
    print_result,
    traced_example,
)
from llama_index.core.llms import ChatMessage


def main() -> None:
    context = create_respan(
        app_name="llama-index-private", example_name="10_private_content"
    )
    previous = os.environ.get("TRACELOOP_TRACE_CONTENT")
    try:
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
        with traced_example(context, root_span_name=context.example_name):
            response = build_llm(context.settings).chat(
                [ChatMessage(role="user", content="private-fixture-prompt")]
            )
            vector = build_embedding_model(context.settings).get_text_embedding(
                "private-embedding-input"
            )
        print_result("Private operations completed", bool(response) and bool(vector))
    finally:
        if previous is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = previous


if __name__ == "__main__":
    main()
