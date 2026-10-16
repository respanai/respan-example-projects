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

EXAMPLE_NAME = "responses"


@workflow(name=workflow_name(EXAMPLE_NAME))
def trace_responses(prompt: str):
    client = make_client()
    try:
        response = client.responses.create(
            model="fixture-responses",
            input=prompt,
            tools=[
                {
                    "type": "function",
                    "name": "weather",
                    "parameters": {"type": "object"},
                }
            ],
        )
        stream = client.responses.create(
            model="fixture-responses", input=prompt, stream=True
        )
        completed = next(
            event.response for event in stream if event.type == "response.completed"
        )
        list(stream)
        return {
            "native_call_id": response.output[1].call_id,
            "stream_tokens": completed.usage.input_tokens,
        }
    finally:
        client.close()


def main():
    run = marker()
    respan = make_respan(EXAMPLE_NAME, run)
    try:
        with example_attributes(EXAMPLE_NAME, run, execution_id(), mode="fixture"):
            print_result(EXAMPLE_NAME, run, trace_responses("Describe the weather."))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
