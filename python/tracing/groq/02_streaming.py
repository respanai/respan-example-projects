from __future__ import annotations

from _shared import (
    example_attributes,
    make_client,
    make_custom_identifier,
    make_respan,
    model_name,
    print_result,
    set_workflow_input,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "streaming"


@workflow(name=workflow_name(EXAMPLE_NAME))
def _streaming_workflow(client) -> str:
    prompt = "Write a four-line checklist for reliable LLM traces."
    set_workflow_input(prompt)
    stream = client.chat.completions.create(
        model=model_name(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        stream=True,
    )
    chunks: list[str] = []
    for chunk in stream:
        content = chunk.choices[0].delta.content if chunk.choices else None
        if content:
            chunks.append(content)
    stream.close()
    return "".join(chunks)


def run_streaming() -> None:
    respan = make_respan(EXAMPLE_NAME)
    client = make_client()
    custom_identifier = make_custom_identifier(EXAMPLE_NAME)
    text = ""

    try:
        with example_attributes(EXAMPLE_NAME, custom_identifier):
            print(f"custom_identifier={custom_identifier}", flush=True)
            print(f"workflow_name={workflow_name(EXAMPLE_NAME)}", flush=True)
            text = _streaming_workflow(client)
    finally:
        client.close()
        respan.shutdown()

    print_result(EXAMPLE_NAME, custom_identifier, text)


if __name__ == "__main__":
    run_streaming()
