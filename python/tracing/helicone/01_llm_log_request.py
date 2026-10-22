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

EXAMPLE = "llm-log-request"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger(
    headers={
        "Helicone-Session-Name": "constructor-session",
        "Helicone-Property-Tier": "deterministic",
        "Authorization": "Bearer local-constructor-secret",
    }
)


@workflow(name="helicone_llm_log_request")
def run(prompt: str) -> str:
    request = {
        "model": "local-helicone-chat",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                        "metadata": {
                            "accessToken": "camel-access-sentinel",
                            "refreshToken": "camel-refresh-sentinel",
                            "clientSecret": "camel-client-sentinel",
                            "promptTokens": 101,
                            "completionTokens": 202,
                            "tokenCount": 303,
                            "tokenizer": "fixture-tokenizer",
                        },
                    }
                ],
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "lookup_documentation",
                    "description": "Look up one documentation topic.",
                    "parameters": {
                        "type": "object",
                        "properties": {"topic": {"type": "string"}},
                        "required": ["topic"],
                    },
                },
            }
        ],
    }

    def operation(recorder):
        response = {
            "model": "local-helicone-chat",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call-helicone-docs",
                                "type": "function",
                                "function": {
                                    "name": "lookup_documentation",
                                    "arguments": '{"topic":"manual logging"}',
                                },
                            }
                        ],
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 8,
                "completion_tokens": 6,
                "total_tokens": 14,
            },
        }
        recorder.append_results(response)
        return response["choices"][0]["message"]["tool_calls"][0]["function"]["name"]

    return logger.log_request(
        request=request,
        operation=operation,
        provider="openai",
        additional_headers={
            "Helicone-Session-Id": f"session-{RUN_MARKER}",
            "Helicone-User-Id": "example-user",
            "Helicone-Property-Environment": "deterministic",
        },
    )


try:
    with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
        output = run("Find the manual logging documentation.")
    assert_local_logs(1, path_suffix="/oai/v1/log")
    print_result(EXAMPLE, RUN_MARKER, {"output": output, "local_logs": 1})
finally:
    finish_respan(respan)
