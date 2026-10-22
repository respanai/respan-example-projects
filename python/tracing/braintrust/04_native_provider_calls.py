"""Real released Braintrust/OpenAI wrappers with controlled HTTP/tool responses."""

from _fixtures import client_context
from _shared import (
    create_braintrust_logger,
    create_respan,
    flush_and_shutdown,
    new_run_id,
    print_trace_lookup,
    workflow_context,
)

NAME = "04_native_provider_calls"
WORKFLOW = "Braintrust Native Provider"


def main():
    marker = new_run_id(NAME)
    respan = create_respan(workflow_name=WORKFLOW, run_id=marker, example_name=NAME)
    logger = create_braintrust_logger(workflow_name=WORKFLOW)
    try:
        with (
            workflow_context(
                respan, workflow_name=WORKFLOW, run_id=marker, example_name=NAME
            ),
            logger.start_span(name=WORKFLOW, type="eval"),
            client_context() as client,
        ):
            result = client.chat.completions.create(
                model="fixture-model",
                messages=[
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "historical-id",
                                "type": "function",
                                "function": {
                                    "name": "lookup",
                                    "arguments": '{"value":1}',
                                },
                            }
                        ],
                    },
                    {
                        "role": "tool",
                        "content": "past result",
                        "tool_call_id": "historical-id",
                    },
                    {"role": "user", "content": "lookup controlled fixture"},
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "lookup",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    f"field_{i}": {"type": "string"} for i in range(100)
                                },
                            },
                        },
                    }
                ],
            )
            assert result.choices[0].message.tool_calls[0].id == "current-source-id"
            stream = client.chat.completions.create(
                model="fixture-model",
                messages=[{"role": "user", "content": "stream fixture"}],
                stream=True,
                stream_options={"include_usage": True},
            )
            chunks = list(stream)
            assert chunks[0].choices[0].delta.content == "controlled stream"
        print_trace_lookup(workflow_name=WORKFLOW, run_id=marker)
    finally:
        flush_and_shutdown(respan, logger)


if __name__ == "__main__":
    main()
