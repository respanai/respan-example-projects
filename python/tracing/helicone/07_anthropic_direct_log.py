from __future__ import annotations

import time

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

EXAMPLE = "anthropic-direct-log"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_anthropic_direct_log")
def run(prompt: str) -> str:
    start = time.time()
    response = {
        "model": "local-claude",
        "role": "assistant",
        "content": [
            {"type": "text", "text": "I will check the documentation."},
            {
                "type": "tool_use",
                "id": "toolu-helicone-docs",
                "name": "lookup_documentation",
                "input": {"topic": "manual logging"},
            },
        ],
        "usage": {
            "input_tokens": 11,
            "output_tokens": 5,
            "cache_read_input_tokens": 7,
        },
    }
    logger.send_log(
        provider="anthropic",
        request={
            "model": "local-claude",
            "system": [
                {"type": "text", "text": "Use documentation tools."},
                {"type": "text", "text": "Preserve structured blocks."},
            ],
            "messages": [
                {"role": "user", "content": "Find an older tracing topic."},
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "I used a previous lookup."},
                        {
                            "type": "tool_use",
                            "id": "toolu-history-tracing",
                            "name": "lookup_documentation",
                            "input": {"topic": "tracing basics"},
                        },
                    ],
                },
                {"role": "user", "content": prompt},
            ],
            "tools": [
                {
                    "name": "lookup_documentation",
                    "description": "Look up a documentation topic.",
                    "input_schema": {
                        "type": "object",
                        "properties": {"topic": {"type": "string"}},
                        "required": ["topic"],
                    },
                }
            ],
        },
        response=response,
        options={
            "start_time": start,
            "end_time": time.time(),
            "time_to_first_token_ms": 12.5,
            "additional_headers": {"Helicone-Property-Mode": "direct"},
        },
    )
    return response["content"][1]["name"]


try:
    with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
        tool_name = run("Find the manual logging documentation.")
    assert_local_logs(1, path_suffix="/anthropic/v1/log")
    print_result(EXAMPLE, RUN_MARKER, {"tool_name": tool_name, "local_logs": 1})
finally:
    finish_respan(respan)
