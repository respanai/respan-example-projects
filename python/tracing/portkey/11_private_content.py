import os

from _shared import (
    example_attributes,
    execution_id,
    finish_respan,
    make_client,
    make_respan,
    marker,
    print_result,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "private-content"


@workflow(name=workflow_name(EXAMPLE_NAME))
def trace_private(prompt: str):
    client = make_client()
    try:
        result = client.chat.completions.create(
            model="fixture-model", messages=[{"role": "user", "content": prompt}]
        )
        list(
            client.chat.completions.create(
                model="fixture-model",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
        )
        client.embeddings.create(model="fixture-embedding", input=prompt)
        return {"native_result_type": type(result).__name__}
    finally:
        client.close()


def main():
    previous = os.environ.get("TRACELOOP_TRACE_CONTENT")
    os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
    run = marker()
    respan = make_respan(EXAMPLE_NAME, run, capture_content=False)
    try:
        with example_attributes(
            EXAMPLE_NAME, run, execution_id(), mode="fixture-private"
        ):
            print_result(EXAMPLE_NAME, run, trace_private("Private fixture text."))
    finally:
        finish_respan(respan)
        if previous is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = previous


if __name__ == "__main__":
    main()
