import httpx
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

EXAMPLE_NAME = "stream-error"


class FailureStream(httpx.SyncByteStream):
    def __iter__(self):
        yield b'data: {"id":"fixture-chunk","object":"chat.completion.chunk","created":1,"model":"fixture-model","choices":[{"index":0,"delta":{"content":"partial"}}]}\n\n'
        raise httpx.ReadError("Controlled stream transport failure.")


@workflow(name=workflow_name(EXAMPLE_NAME))
def trace_stream_error(prompt: str):
    client = make_client()
    client.openai_client._client._transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            stream=FailureStream(),
            headers={"content-type": "text/event-stream"},
            request=request,
        )
    )
    try:
        list(
            client.chat.completions.create(
                model="fixture-model",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
        )
    finally:
        client.close()


def main():
    run = marker()
    respan = make_respan(EXAMPLE_NAME, run)
    try:
        try:
            with example_attributes(
                EXAMPLE_NAME, run, execution_id(), mode="fixture-error"
            ):
                trace_stream_error("Exercise stream failure.")
        except httpx.ReadError as error:
            print_result(EXAMPLE_NAME, run, {"expected_error": type(error).__name__})
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
