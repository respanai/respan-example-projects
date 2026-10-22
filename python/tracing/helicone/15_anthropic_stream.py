from __future__ import annotations

from _shared import (
    assert_local_logs,
    example_attributes,
    execution_id,
    finish_respan,
    make_logger,
    make_respan,
    marker,
    print_result,
)
from respan import workflow

EXAMPLE = "anthropic-stream"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_anthropic_stream")
def run(prompt: str) -> str:
    def operation(recorder):
        events = [
            {
                "type": "message_start",
                "message": {
                    "model": "claude-stream-response",
                    "usage": {
                        "input_tokens": 10,
                        "cache_read_input_tokens": 4,
                    },
                },
            },
            {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            },
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": "Streaming tool call."},
            },
            {
                "type": "content_block_start",
                "index": 1,
                "content_block": {
                    "type": "tool_use",
                    "id": "toolu-stream-example",
                    "name": "lookup_documentation",
                    "input": {},
                },
            },
            {
                "type": "content_block_delta",
                "index": 1,
                "delta": {
                    "type": "input_json_delta",
                    "partial_json": '{"topic":"streaming"}',
                },
            },
            {"type": "message_delta", "usage": {"output_tokens": 5}},
        ]
        recorder.append_results({"chunks": events, "time_to_first_token_ms": 9.75})
        return "lookup_documentation"

    return logger.log_request(
        request={
            "model": "claude-stream-request",
            "system": [{"type": "text", "text": "Use structured streaming."}],
            "messages": [{"role": "user", "content": prompt}],
            "tools": [
                {
                    "name": "lookup_documentation",
                    "input_schema": {"type": "object"},
                }
            ],
            "stream": True,
        },
        operation=operation,
        provider="anthropic",
    )


try:
    with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
        tool_name = run("Stream a documentation lookup.")
    assert_local_logs(1, path_suffix="/anthropic/v1/log")
    print_result(EXAMPLE, RUN_MARKER, {"tool_name": tool_name, "local_logs": 1})
finally:
    finish_respan(respan)
