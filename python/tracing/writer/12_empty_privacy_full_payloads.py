from _fixtures import NativeRuntime, invoke
from _shared import example_attributes, finish_respan, make_respan
from opentelemetry import context
from respan import workflow
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


@workflow(name="writer_empty_privacy_full_payloads")
def scenario():
    with NativeRuntime(empty=True).client() as client:
        assert invoke(client, "chat").choices == []
    schema = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "private_key": {"type": "string", "default": "controlled secret"},
                    "zero": {"type": "integer", "default": 0},
                    "flag": {"type": "boolean", "default": False},
                },
            },
        },
    }
    with NativeRuntime(vector=True).client() as client:
        response = client.chat.chat(
            model="native-writer",
            messages=(
                {"role": "user", "content": "x" * 10000 + str(i)} for i in range(75)
            ),
            tools=[schema],
            temperature=0,
        )
        assert len(response.native_vector) == 5001
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    try:
        with NativeRuntime().client() as client:
            invoke(client, "chat")
    finally:
        context.detach(token)
    with NativeRuntime().client() as client:
        stream = invoke(client, "chat", stream=True)
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        context.detach(token)
        stream.close()
    return (
        "full empty feedback,75history,5001native extra vector and irreversible privacy"
    )


def run():
    respan = make_respan("empty-privacy-full")
    try:
        with example_attributes("empty-privacy-full"):
            print(scenario())
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run()
