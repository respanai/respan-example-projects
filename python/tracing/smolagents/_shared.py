"""Shared setup for smolagents Respan examples."""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from respan import Respan, propagate_attributes
from respan_instrumentation_smolagents import SmolagentsInstrumentor
from smolagents import Model
from smolagents.models import (
    ChatMessage,
    ChatMessageStreamDelta,
    ChatMessageToolCall,
    ChatMessageToolCallFunction,
    ChatMessageToolCallStreamDelta,
    MessageRole,
)
from smolagents.monitoring import TokenUsage

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env", override=False)

DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
DEFAULT_CUSTOMER_IDENTIFIER = "smolagents-example-user"
DEFAULT_RUN_ID = datetime.now(timezone.utc).strftime("smolagents-%Y%m%d-%H%M%S")


def _required_env(name: str, fallback_name: str | None = None) -> str:
    value = os.getenv(name)
    if value:
        return value
    if fallback_name:
        fallback_value = os.getenv(fallback_name)
        if fallback_value:
            return fallback_value
    raise RuntimeError(
        f"Missing {name} in {REPO_ROOT / '.env'}"
        + (f" or {fallback_name}" if fallback_name else "")
    )


def _gateway_model_id() -> str:
    model = os.getenv("RESPAN_MODEL", "gpt-4o-mini")
    if "/" in model:
        return model
    return f"openai/{model}"


def response(content=None, *, calls=None) -> ChatMessage:
    # This is an explicit controlled model boundary, not provider usage evidence.
    return ChatMessage(
        role=MessageRole.ASSISTANT,
        content=content,
        tool_calls=calls,
        token_usage=TokenUsage(input_tokens=11, output_tokens=7),
        raw={
            "usage": {
                "prompt_tokens_details": {"cached_tokens": 3},
                "completion_tokens_details": {"reasoning_tokens": 2},
            }
        },
    )


def tool_call(name: str, arguments: dict, identifier: str) -> ChatMessageToolCall:
    return ChatMessageToolCall(
        id=identifier,
        type="function",
        function=ChatMessageToolCallFunction(name=name, arguments=arguments),
    )


class FixtureModel(Model):
    """Released Model interface with deterministic responses and usage fixtures."""

    provider = "fixture"

    def __init__(self, replies):
        super().__init__(model_id="fixture-smolagents")
        self.replies = iter(replies)
        self.received_messages = []

    def generate(self, messages, tools_to_call_from=None, **kwargs):
        self.received_messages.append(messages)
        value = next(self.replies)
        if isinstance(value, BaseException):
            raise value
        return value

    def generate_stream(self, messages, tools_to_call_from=None, **kwargs):
        message = self.generate(
            messages, tools_to_call_from=tools_to_call_from, **kwargs
        )
        if message.content:
            middle = max(1, len(message.content) // 2)
            yield ChatMessageStreamDelta(content=message.content[:middle])
            yield ChatMessageStreamDelta(content=message.content[middle:])
        for index, call in enumerate(message.tool_calls or []):
            import json

            arguments = json.dumps(call.function.arguments)
            middle = max(1, len(arguments) // 2)
            yield ChatMessageStreamDelta(
                tool_calls=[
                    ChatMessageToolCallStreamDelta(
                        index=index,
                        id=call.id,
                        type="function",
                        function=ChatMessageToolCallFunction(
                            name=call.function.name, arguments=arguments[:middle]
                        ),
                    )
                ]
            )
            yield ChatMessageStreamDelta(
                tool_calls=[
                    ChatMessageToolCallStreamDelta(
                        index=index,
                        function=ChatMessageToolCallFunction(
                            name="", arguments=arguments[middle:]
                        ),
                    )
                ]
            )
        yield ChatMessageStreamDelta(token_usage=message.token_usage)


def build_model(scenario: str = "code"):
    mode = os.getenv("SMOLAGENTS_MODEL_MODE", "fixture")
    if mode == "fixture":
        if scenario == "code":
            return FixtureModel(
                [
                    response(
                        "Thought: use the local fact.\n<code>final_answer(get_city_population('Paris'))</code>"
                    )
                ]
            )
        if scenario == "invoice":
            return FixtureModel(
                [
                    response(
                        calls=[
                            tool_call(
                                "calculate_invoice_total",
                                {"unit_price_usd": 9, "quantity": 7},
                                "invoice-1",
                            )
                        ]
                    ),
                    response(
                        calls=[
                            tool_call(
                                "final_answer",
                                {"answer": "7 items at $9 each cost $63."},
                                "invoice-answer",
                            )
                        ]
                    ),
                ]
            )
        return FixtureModel(
            [
                response(
                    calls=[
                        tool_call(
                            "final_answer",
                            {"answer": "streamed smolagents tracing works"},
                            "stream-answer",
                        )
                    ]
                )
            ]
        )
    if mode != "live":
        raise ValueError("SMOLAGENTS_MODEL_MODE must be fixture or live")
    from smolagents import LiteLLMModel

    return LiteLLMModel(
        model_id=_gateway_model_id(),
        api_key=_required_env("RESPAN_GATEWAY_API_KEY", "RESPAN_API_KEY"),
        api_base=os.getenv(
            "RESPAN_GATEWAY_BASE_URL",
            os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL),
        ),
    )


def build_respan(example_name: str, workflow_name: str) -> Respan:
    trace_api_key = _required_env("RESPAN_API_KEY", "RESPAN_GATEWAY_API_KEY")
    respan_base_url = os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL)
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID", DEFAULT_RUN_ID)

    return Respan(
        api_key=trace_api_key,
        base_url=respan_base_url,
        app_name=f"smolagents-{example_name}",
        instrumentations=[SmolagentsInstrumentor()],
        customer_identifier=os.getenv(
            "RESPAN_EXAMPLE_CUSTOMER_IDENTIFIER",
            DEFAULT_CUSTOMER_IDENTIFIER,
        ),
        metadata={
            "integration": "smolagents",
            "example_set": "smolagents",
            "example": example_name,
            "run_id": run_id,
            "example_run_id": run_id,
            "workflow_name": workflow_name,
        },
        environment="examples",
        is_batching_enabled=False,
        log_level="WARNING",
    )


@contextmanager
def example_attributes(example_name: str, workflow_name: str):
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID", DEFAULT_RUN_ID)
    with propagate_attributes(
        trace_group_identifier=workflow_name,
        metadata={
            "integration": "smolagents",
            "example_set": "smolagents",
            "example": example_name,
            "run_id": run_id,
            "example_run_id": run_id,
            "workflow_name": workflow_name,
        },
    ):
        yield
