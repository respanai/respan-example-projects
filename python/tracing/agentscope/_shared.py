"""Shared setup for AgentScope Respan examples."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentscope.formatter import OpenAIChatFormatter
from agentscope.message import TextBlock, ToolCallBlock
from agentscope.model import ChatResponse, ChatUsage
from dotenv import load_dotenv
from respan import Respan, propagate_attributes
from respan_instrumentation_agentscope import AgentScopeInstrumentor

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env", override=False)

DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
DEFAULT_CUSTOMER_IDENTIFIER = "agentscope-example-user"
DEFAULT_RUN_ID = datetime.now(timezone.utc).strftime("agentscope-%Y%m%d-%H%M%S")
DEFAULT_GROUP_IDENTIFIER = "otel2-python-agent-frameworks"


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    raise RuntimeError(f"Missing {name} in {REPO_ROOT / '.env'}")


def build_respan(
    example_name: str,
    workflow_name: str,
    *,
    models: Sequence[Any] | None = None,
    capture_content: bool = True,
) -> Respan:
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID", DEFAULT_RUN_ID)
    group_identifier = os.getenv(
        "RESPAN_EXAMPLE_GROUP_ID",
        DEFAULT_GROUP_IDENTIFIER,
    )
    return Respan(
        api_key=_required_env("RESPAN_API_KEY"),
        base_url=os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL),
        app_name=f"agentscope-{example_name}",
        instrumentations=[
            AgentScopeInstrumentor(models=models, capture_content=capture_content)
        ],
        customer_identifier=os.getenv(
            "RESPAN_EXAMPLE_CUSTOMER_IDENTIFIER",
            DEFAULT_CUSTOMER_IDENTIFIER,
        ),
        metadata={
            "integration": "agentscope",
            "example": example_name,
            "run_id": run_id,
            "workflow_name": workflow_name,
        },
        thread_identifier=f"{group_identifier}:{example_name}",
        environment="examples",
        is_batching_enabled=False,
    )


@contextmanager
def example_scope(example_name: str):
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID", DEFAULT_RUN_ID)
    group_identifier = os.getenv(
        "RESPAN_EXAMPLE_GROUP_ID",
        DEFAULT_GROUP_IDENTIFIER,
    )
    with propagate_attributes(
        trace_group_identifier=group_identifier,
        metadata={
            "run_id": run_id,
            "integration": "agentscope",
            "example": example_name,
        },
        custom_identifier=f"{run_id}:{example_name}",
    ):
        yield


def usage(input_tokens: int = 10, output_tokens: int = 6) -> ChatUsage:
    return ChatUsage(input_tokens=input_tokens, output_tokens=output_tokens, time=0.01)


def text_response(
    text: str, *, input_tokens: int = 10, output_tokens: int = 6
) -> ChatResponse:
    return ChatResponse(
        content=[TextBlock(text=text)],
        is_last=True,
        usage=usage(input_tokens=input_tokens, output_tokens=output_tokens),
    )


def tool_call_response(
    *,
    call_id: str,
    name: str,
    arguments: dict[str, Any],
) -> ChatResponse:
    return ChatResponse(
        content=[
            ToolCallBlock(
                id=call_id,
                name=name,
                input=json.dumps(arguments, separators=(",", ":")),
            )
        ],
        is_last=True,
        usage=usage(input_tokens=14, output_tokens=4),
    )


class ScriptedChatModel:
    """Small deterministic AgentScope-compatible chat model."""

    provider = "scripted"
    stream = False
    max_retries = 0
    retry_delay = 0.0
    context_size = 8192

    def __init__(
        self,
        *,
        model: str,
        responses: list[
            ChatResponse | Callable[[list[Any], list[dict] | None], ChatResponse]
        ],
    ) -> None:
        self.model = model
        self.formatter = OpenAIChatFormatter()
        self._responses = list(responses)

    async def __call__(
        self,
        messages: list[Any],
        tools: list[dict] | None = None,
        tool_choice: Any | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        if not self._responses:
            return text_response("No scripted responses remain.")
        response = self._responses.pop(0)
        if callable(response):
            return response(messages, tools)
        return response

    async def count_tokens(
        self,
        messages: list[Any],
        tools: list[dict] | None = None,
    ) -> int:
        return sum(len(str(message)) for message in messages) // 4 + len(tools or [])


class FailingChatModel(ScriptedChatModel):
    async def __call__(
        self,
        messages: list[Any],
        tools: list[dict] | None = None,
        tool_choice: Any | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        raise RuntimeError("deterministic AgentScope model failure")
