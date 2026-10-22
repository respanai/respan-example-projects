"""Shared setup for Microsoft Agent Framework tracing examples."""

import asyncio
import inspect
import os
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from respan import Respan
from respan_instrumentation_microsoft_agent_framework import (
    MicrosoftAgentFrameworkInstrumentor,
)

EXAMPLE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_ROOT.parents[2]
DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
DEFAULT_MODEL = "gpt-4.1-nano"
DEFAULT_RUN_ID = datetime.now(timezone.utc).strftime(
    "microsoft-agent-framework-%Y%m%d-%H%M%S"
)
EXAMPLE_SET = "microsoft-agent-framework"


def load_gateway_env() -> tuple[str, str, str, str, str]:
    """Load the repo-root env file and configure OpenAI-compatible gateway env."""
    requested_run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID")
    load_dotenv(REPO_ROOT / ".env", override=False)
    if requested_run_id:
        os.environ["RESPAN_EXAMPLE_RUN_ID"] = requested_run_id

    respan_api_key = os.getenv("RESPAN_API_KEY") or os.getenv("RESPAN_GATEWAY_API_KEY")
    if not respan_api_key:
        raise RuntimeError("RESPAN_API_KEY or RESPAN_GATEWAY_API_KEY is required")

    respan_base_url = os.getenv("RESPAN_BASE_URL") or DEFAULT_RESPAN_BASE_URL
    gateway_api_key = os.getenv("RESPAN_GATEWAY_API_KEY") or respan_api_key
    gateway_base_url = os.getenv("RESPAN_GATEWAY_BASE_URL") or respan_base_url
    model = os.getenv("RESPAN_MODEL", DEFAULT_MODEL)

    os.environ["OPENAI_API_KEY"] = gateway_api_key
    os.environ["OPENAI_BASE_URL"] = gateway_base_url
    os.environ["OPENAI_MODEL"] = model
    os.environ["OPENAI_CHAT_MODEL"] = model
    os.environ["OPENAI_MODEL_ID"] = model
    os.environ["OPENAI_CHAT_MODEL_ID"] = model
    return respan_api_key, respan_base_url, gateway_api_key, gateway_base_url, model


def create_openai_chat_client():
    """Create a chat-completions Agent Framework OpenAI client."""
    from agent_framework.openai import OpenAIChatCompletionClient
    from openai import AsyncOpenAI

    _respan_key, _respan_url, gateway_key, gateway_url, model = load_gateway_env()
    async_client = AsyncOpenAI(
        api_key=gateway_key,
        base_url=gateway_url,
        timeout=float(os.getenv("RESPAN_MAF_LIVE_TIMEOUT_SECONDS", "45")),
        max_retries=0,
    )
    return OpenAIChatCompletionClient(
        async_client=async_client,
        model=model,
    )


def create_deterministic_chat_client():
    """Create a real Agent Framework OpenAI client with local provider results."""
    from agent_framework import ChatResponse, Content, Message
    from agent_framework.openai import OpenAIChatCompletionClient

    class DeterministicOpenAIChatCompletionClient(OpenAIChatCompletionClient):
        def __init__(self) -> None:
            super().__init__(
                api_key="deterministic-example",
                base_url="https://deterministic.invalid/v1",
                model=DEFAULT_MODEL,
            )
            self._responses = deque(
                [
                    ChatResponse(
                        messages=Message(
                            "assistant",
                            [
                                Content.from_function_call(
                                    "weather-call-1",
                                    "lookup_weather",
                                    arguments={"city": "Seattle"},
                                )
                            ],
                        ),
                        model=DEFAULT_MODEL,
                        usage_details={
                            "input_token_count": 18,
                            "output_token_count": 7,
                        },
                    ),
                    ChatResponse(
                        messages=Message(
                            "assistant",
                            [Content.from_text("Seattle is sunny and 72F.")],
                        ),
                        model=DEFAULT_MODEL,
                        usage_details={
                            "input_token_count": 29,
                            "output_token_count": 8,
                        },
                    ),
                ]
            )

        def _inner_get_response(
            self,
            *,
            messages: Any,
            options: Any,
            stream: bool = False,
            **kwargs: Any,
        ) -> Any:
            if stream:
                raise NotImplementedError("The deterministic example is non-streaming")

            async def get_response() -> Any:
                return self._responses.popleft()

            return get_response()

    return DeterministicOpenAIChatCompletionClient()


def create_respan(app_name: str, *, capture_content: bool = True) -> Respan:
    respan_api_key, respan_base_url, _gateway_key, _gateway_url, _model = (
        load_gateway_env()
    )
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID", DEFAULT_RUN_ID)
    return Respan(
        api_key=respan_api_key,
        base_url=respan_base_url,
        app_name=app_name,
        instrumentations=[
            MicrosoftAgentFrameworkInstrumentor(capture_content=capture_content),
        ],
        metadata={
            "integration": EXAMPLE_SET,
            "example": app_name,
            "example_run_id": run_id,
            "run_id": run_id,
        },
        environment="examples",
        is_batching_enabled=False,
        is_auto_instrument=False,
        log_level=os.getenv("RESPAN_LOG_LEVEL", "WARNING"),
    )


def workflow_attributes(workflow_name: str) -> dict[str, object]:
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID", DEFAULT_RUN_ID)
    return {
        "trace_group_identifier": run_id,
        "custom_identifier": f"{workflow_name}-{run_id}",
        "metadata": {
            "integration": EXAMPLE_SET,
            "example": workflow_name,
            "example_run_id": run_id,
            "run_id": run_id,
            "workflow_name": workflow_name,
        },
    }


def finish_respan(respan: Respan) -> None:
    try:
        respan.flush()
    finally:
        respan.shutdown()


async def close_chat_client(client: Any) -> None:
    raw_client = getattr(client, "client", None)
    close = getattr(raw_client, "close", None)
    if not callable(close):
        return
    result = close()
    if inspect.isawaitable(result):
        await asyncio.wait_for(
            result,
            timeout=float(os.getenv("RESPAN_MAF_CLOSE_TIMEOUT_SECONDS", "5")),
        )


def live_example_enabled() -> bool:
    return os.getenv("RESPAN_MAF_RUN_LIVE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def create_streaming_fixture_client(mode="complete"):
    """Native framework client with local stream updates and deterministic usage."""
    from agent_framework import (
        BaseChatClient,
        ChatResponse,
        ChatResponseUpdate,
        Content,
        Message,
        ResponseStream,
    )
    from agent_framework.observability import ChatTelemetryLayer

    class FixtureClient(ChatTelemetryLayer, BaseChatClient):
        OTEL_PROVIDER_NAME = "fixture"

        def __init__(self):
            self.model = "respan-maf-fixture"
            self.closed = False
            super().__init__()

        def service_url(self):
            return "https://fixture.invalid/v1"

        def _inner_get_response(self, *, messages, options, stream=False, **kwargs):
            async def response():
                return ChatResponse(
                    messages=Message(
                        "assistant", [Content.from_text("Fixture answer")]
                    ),
                    model=self.model,
                    usage_details={
                        "input_token_count": 7,
                        "output_token_count": 3,
                        "cache_read_input_token_count": 2,
                        "reasoning_output_token_count": 1,
                    },
                )

            async def updates():
                try:
                    yield ChatResponseUpdate(
                        role="assistant",
                        contents=[Content.from_text("Fixture ")],
                        model=self.model,
                    )
                    if mode == "error":
                        raise RuntimeError("Controlled fixture stream failure")
                    if mode == "cancel":
                        await asyncio.Event().wait()
                    yield ChatResponseUpdate(
                        role="assistant",
                        contents=[
                            Content.from_text("answer"),
                            Content.from_usage(
                                {"input_token_count": 7, "output_token_count": 3}
                            ),
                        ],
                        model=self.model,
                    )
                finally:
                    self.closed = True

            return (
                ResponseStream(updates(), finalizer=ChatResponse.from_updates)
                if stream
                else response()
            )

    return FixtureClient()
