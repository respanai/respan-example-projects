from _fixtures import NativeRuntime, invoke
from _shared import example_attributes, finish_respan, make_respan
from respan import workflow
from writerai import APIError


@workflow(name="writer_retry_stream_error_close")
def scenario():
    runtime = NativeRuntime(retry=True)
    with runtime.client(max_retries=1) as client:
        invoke(client, "chat")
    assert len(runtime.requests) == runtime.response_callbacks == 2
    with NativeRuntime().client() as client:
        source = invoke(client, "chat", stream=True)
        with source as native:
            assert native is source
            next(native)
        invoke(client, "chat", stream=True).close()
    with NativeRuntime(stream_error=True).client() as client:
        try:
            list(invoke(client, "chat", stream=True))
        except APIError:
            pass
        else:
            raise AssertionError("native SSE event:error must raise")
    return "native retry,callbacks,contexts,unreadclose and partial stream error"


def run():
    respan = make_respan("retry-stream-error-close")
    try:
        with example_attributes("retry-stream-error-close"):
            print(scenario())
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run()
