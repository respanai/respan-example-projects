"""Shared setup and deterministic Mirascope 2.x provider for the examples."""

from __future__ import annotations

import inspect
import os
from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from mirascope import llm
from respan import Respan
from respan_instrumentation_mirascope import MirascopeInstrumentor

EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parents[2]
DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
DEFAULT_MODEL = "gpt-4.1-nano"
DEFAULT_RUN_ID = datetime.now(timezone.utc).strftime("mirascope-%Y%m%dT%H%M%SZ")


def load_example_env() -> tuple[str, str, str, str]:
    """Load Respan export and OpenAI-compatible gateway settings."""
    load_dotenv(REPO_ROOT / ".env", override=False)
    api_key = os.getenv("RESPAN_API_KEY")
    if not api_key:
        raise RuntimeError(f"RESPAN_API_KEY is required in {REPO_ROOT / '.env'}")
    base_url = os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL)
    gateway_key = os.getenv("RESPAN_GATEWAY_API_KEY", api_key)
    gateway_url = os.getenv("RESPAN_GATEWAY_BASE_URL", base_url)
    return api_key, base_url, gateway_key, gateway_url


def create_respan(app_name: str, *, capture_content: bool = True) -> Respan:
    """Create a Respan runtime linked to the local Mirascope instrumentor."""
    api_key, base_url, _gateway_key, _gateway_url = load_example_env()
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID", DEFAULT_RUN_ID)
    return Respan(
        api_key=api_key,
        base_url=base_url,
        app_name=app_name,
        instrumentations=[
            MirascopeInstrumentor(capture_content=capture_content),
        ],
        metadata={
            "integration": "mirascope",
            "example": app_name,
            "example_run_id": run_id,
            "run_id": run_id,
        },
        environment="examples",
        is_batching_enabled=False,
    )


def workflow_attributes(workflow_name: str, script_name: str) -> dict[str, object]:
    """Return stable grouping plus a unique root identifier for one example."""
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID", DEFAULT_RUN_ID)
    return {
        "trace_group_identifier": f"{workflow_name}-{run_id}",
        "custom_identifier": f"{workflow_name}-{uuid4().hex[:8]}",
        "metadata": {
            "example": "mirascope",
            "example_run_id": run_id,
            "run_id": run_id,
            "script": script_name,
            "workflow_name": workflow_name,
        },
    }


def finish_respan(respan: Respan) -> None:
    """Force pending spans out and release instrumentation patches."""
    try:
        respan.flush()
    finally:
        respan.shutdown()


def _assistant_message(
    *,
    model_id: str,
    content: str | llm.ToolCall,
) -> Any:
    return llm.messages.assistant(
        content,
        provider_id="deterministic",
        model_id=model_id,
        provider_model_name=model_id.split("/", 1)[-1],
    )


class DeterministicProvider:
    """Small provider that returns real Mirascope response and stream objects."""

    id = "deterministic"
    default_scope = "deterministic/"

    def __init__(self, *, fail_status: int | None = None) -> None:
        self.fail_status = fail_status
        self.client = None

    def _raise_if_requested(self) -> None:
        if self.fail_status is not None:
            raise llm.ServerError(
                "deterministic Mirascope provider failure",
                provider="deterministic",
                status_code=self.fail_status,
            )

    def call(
        self,
        *,
        model_id: str,
        messages: Sequence[Any],
        toolkit: Any,
        format: Any = None,
        **params: Any,
    ) -> llm.Response:
        self._raise_if_requested()
        content: str | llm.ToolCall
        if toolkit.tools:
            content = llm.ToolCall(
                id="weather-call-1",
                name="lookup_weather",
                args='{"city":"Paris"}',
            )
        else:
            content = "Mirascope deterministic response."
        return llm.Response(
            raw={"fixture": "deterministic"},
            provider_id="deterministic",
            model_id=model_id,
            provider_model_name=model_id.split("/", 1)[-1],
            params=params,
            tools=toolkit,
            format=format,
            input_messages=messages,
            assistant_message=_assistant_message(model_id=model_id, content=content),
            finish_reason=None,
            usage=llm.Usage(input_tokens=24, output_tokens=10),
        )

    async def call_async(self, **kwargs: Any) -> llm.AsyncResponse:
        response = self.call(**kwargs)
        return llm.AsyncResponse(
            raw=response.raw,
            provider_id=response.provider_id,
            model_id=response.model_id,
            provider_model_name=response.provider_model_name,
            params=response.params,
            tools=response.toolkit,
            format=response.format,
            input_messages=response.messages[:-1],
            assistant_message=response.messages[-1],
            finish_reason=response.finish_reason,
            usage=response.usage,
        )

    def stream(
        self,
        *,
        model_id: str,
        messages: Sequence[Any],
        toolkit: Any,
        format: Any = None,
        **params: Any,
    ) -> llm.StreamResponse:
        self._raise_if_requested()
        chunks: Iterator[Any] = iter(
            [
                llm.TextStartChunk(),
                llm.TextChunk(delta="Mirascope streaming works."),
                llm.TextEndChunk(),
                llm.UsageDeltaChunk(input_tokens=12, output_tokens=6),
            ]
        )
        return llm.StreamResponse(
            provider_id="deterministic",
            model_id=model_id,
            provider_model_name=model_id.split("/", 1)[-1],
            params=params,
            tools=toolkit,
            format=format,
            input_messages=messages,
            chunk_iterator=chunks,
        )

    async def stream_async(
        self,
        *,
        model_id: str,
        messages: Sequence[Any],
        toolkit: Any,
        format: Any = None,
        **params: Any,
    ) -> llm.AsyncStreamResponse:
        self._raise_if_requested()

        async def chunks() -> AsyncIterator[Any]:
            yield llm.TextStartChunk()
            yield llm.TextChunk(delta="Async Mirascope streaming works.")
            yield llm.TextEndChunk()
            yield llm.UsageDeltaChunk(input_tokens=8, output_tokens=4)

        return llm.AsyncStreamResponse(
            provider_id="deterministic",
            model_id=model_id,
            provider_model_name=model_id.split("/", 1)[-1],
            params=params,
            tools=toolkit,
            format=format,
            input_messages=messages,
            chunk_iterator=chunks(),
        )


def create_deterministic_model(*, fail_status: int | None = None) -> llm.Model:
    """Register the deterministic provider and return a real Mirascope model."""
    provider = DeterministicProvider(fail_status=fail_status)
    llm.register_provider(provider, scope="deterministic/")
    return llm.Model("deterministic/mirascope-2x")


def create_live_model() -> llm.Model:
    """Register Mirascope's OpenAI provider against the configured gateway."""
    from mirascope.llm.providers import OpenAIProvider

    _api_key, _base_url, gateway_key, gateway_url = load_example_env()
    configured_model = os.getenv("RESPAN_MODEL", DEFAULT_MODEL)
    model_id = (
        configured_model if "/" in configured_model else f"openai/{configured_model}"
    )
    if not model_id.endswith(":completions"):
        model_id = f"{model_id}:completions"
    provider = OpenAIProvider(api_key=gateway_key, base_url=gateway_url)
    llm.register_provider(provider, scope="openai/")
    return llm.Model(model_id, max_tokens=64, temperature=0)


def live_example_enabled() -> bool:
    """Require an explicit opt-in for paid provider inference."""
    load_dotenv(REPO_ROOT / ".env", override=False)
    return os.getenv("RESPAN_MIRASCOPE_RUN_LIVE", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def close_model_provider(model: llm.Model) -> None:
    """Close Mirascope provider clients when they expose synchronous close hooks."""
    provider = model.provider
    candidates = [
        getattr(provider, "client", None),
        getattr(getattr(provider, "_completions_provider", None), "client", None),
        getattr(getattr(provider, "_responses_provider", None), "client", None),
    ]
    seen: set[int] = set()
    for candidate in candidates:
        if candidate is None or id(candidate) in seen:
            continue
        seen.add(id(candidate))
        close = getattr(candidate, "close", None)
        if callable(close) and not inspect.iscoroutinefunction(close):
            close()
