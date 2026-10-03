from __future__ import annotations

from _shared import (
    example_attributes,
    make_client,
    make_custom_identifier,
    make_respan,
    model_name,
    print_result,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "stream-content"


@workflow(name=workflow_name(EXAMPLE_NAME))
def _stream_content_workflow(prompt: str) -> str:
    client = make_client()
    chunks: list[str] = []
    for chunk in client.models.generate_content_stream(
        model=model_name(),
        contents=prompt,
    ):
        if chunk.text:
            chunks.append(chunk.text)
    return "".join(chunks)


def run_stream_content() -> None:
    respan = make_respan(EXAMPLE_NAME)
    custom_identifier = make_custom_identifier(EXAMPLE_NAME)
    text = ""

    try:
        with example_attributes(EXAMPLE_NAME, custom_identifier):
            print(f"custom_identifier={custom_identifier}", flush=True)
            print(f"workflow_name={workflow_name(EXAMPLE_NAME)}", flush=True)
            text = _stream_content_workflow(
                "Stream three short bullet points about production tracing."
            )
    finally:
        respan.shutdown()

    print_result(EXAMPLE_NAME, custom_identifier, text)


if __name__ == "__main__":
    run_stream_content()
