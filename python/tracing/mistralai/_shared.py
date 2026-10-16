from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx2 as httpx
from dotenv import load_dotenv
from mistralai.client import Mistral
from respan import Respan, propagate_attributes
from respan_instrumentation_mistralai import MistralAIInstrumentor

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
DEFAULT_MISTRAL_MODEL = "mistral/mistral-small"
EXAMPLE_SET = "mistralai"
DEFAULT_RUN_ID = f"mistralai-{uuid4().hex[:12]}"


def load_root_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def require_respan_api_key() -> str:
    load_root_env()
    api_key = os.getenv("RESPAN_API_KEY")
    if not api_key:
        raise RuntimeError("RESPAN_API_KEY must be set in the repo root .env file")
    return api_key


def gateway_api_key() -> str:
    return os.getenv("RESPAN_GATEWAY_API_KEY") or require_respan_api_key()


def respan_base_url() -> str:
    return os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL).rstrip("/")


def model_name() -> str:
    configured_model = os.getenv("RESPAN_MISTRALAI_MODEL")
    if configured_model:
        return configured_model
    if mistral_api_key():
        return os.getenv("MISTRALAI_MODEL", DEFAULT_MISTRAL_MODEL)
    return os.getenv("RESPAN_MODEL", DEFAULT_MISTRAL_MODEL)


def make_respan(example_name: str) -> Respan:
    api_key = require_respan_api_key()
    run_id = example_run_id()
    return Respan(
        api_key=api_key,
        base_url=respan_base_url(),
        app_name="mistralai-examples",
        instrumentations=[MistralAIInstrumentor()],
        environment=os.getenv("RESPAN_ENVIRONMENT", "example"),
        metadata={
            "integration": EXAMPLE_SET,
            "example": example_name,
            "example_run_id": run_id,
        },
        is_batching_enabled=False,
    )


def mistral_api_key() -> str | None:
    return os.getenv("MISTRAL_API_KEY")


def make_client() -> Mistral:
    if os.getenv("MISTRAL_USE_MOCKS", "").lower() in {"1", "true", "yes"}:

        def handler(request):
            return deterministic_chat_response(
                request,
                content="Mistral SDK 3 fixture response.",
                prompt_tokens=8,
                completion_tokens=5,
            )

        return Mistral(
            api_key="deterministic-example-key",
            client=httpx.Client(transport=httpx.MockTransport(handler)),
            async_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )
    direct_api_key = mistral_api_key()
    if direct_api_key:
        return Mistral(api_key=direct_api_key)

    return Mistral(
        api_key=gateway_api_key(),
        server_url=respan_base_url(),
    )


def make_mock_sync_client(
    handler: Callable[[httpx.Request], httpx.Response],
) -> Mistral:
    """Create a current Mistral SDK client backed by a repeatable HTTP fixture."""
    return Mistral(
        api_key="deterministic-example-key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def make_mock_async_client(
    handler: Callable[[httpx.Request], httpx.Response],
) -> Mistral:
    """Create an async current Mistral SDK client backed by an HTTP fixture."""

    async def async_handler(request: httpx.Request) -> httpx.Response:
        return handler(request)

    return Mistral(
        api_key="deterministic-example-key",
        async_client=httpx.AsyncClient(transport=httpx.MockTransport(async_handler)),
    )


def deterministic_chat_response(
    request: httpx.Request,
    *,
    content: str,
    prompt_tokens: int,
    completion_tokens: int,
    tool_calls: list[dict[str, Any]] | None = None,
) -> httpx.Response:
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return httpx.Response(
        200,
        json={
            "id": "mistralai_example_completion",
            "object": "chat.completion",
            "model": model_name(),
            "created": 1_710_000_000,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            "choices": [
                {
                    "index": 0,
                    "message": message,
                    "finish_reason": "tool_calls" if tool_calls else "stop",
                }
            ],
        },
        request=request,
    )


def deterministic_stream_response(
    request: httpx.Request,
    *,
    fragments: tuple[str, ...],
    prompt_tokens: int,
    completion_tokens: int,
) -> httpx.Response:
    chunks = []
    for index, fragment in enumerate(fragments):
        final = index == len(fragments) - 1
        chunk: dict[str, Any] = {
            "id": "mistralai_example_stream",
            "object": "chat.completion.chunk",
            "model": model_name(),
            "created": 1_710_000_000,
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        **({"role": "assistant"} if index == 0 else {}),
                        "content": fragment,
                    },
                    "finish_reason": "stop" if final else None,
                }
            ],
        }
        if final:
            chunk["usage"] = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            }
        chunks.append(chunk)

    body = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks)
    body += "data: [DONE]\n\n"
    return httpx.Response(
        200,
        content=body,
        headers={"content-type": "text/event-stream"},
        request=request,
    )


def workflow_name(example_name: str) -> str:
    normalized_name = example_name.replace("-", "_")
    return f"mistralai_{normalized_name}"


def make_custom_identifier(example_name: str) -> str:
    return f"mistralai-{example_name}-{uuid4().hex[:8]}"


def example_run_id() -> str:
    """Return the exact shell marker, with a unique fallback for ad-hoc runs."""
    return os.getenv("RESPAN_EXAMPLE_RUN_ID") or DEFAULT_RUN_ID


@contextmanager
def example_attributes(
    example_name: str,
    custom_identifier: str | None = None,
) -> Iterator[str]:
    custom_identifier = custom_identifier or make_custom_identifier(example_name)
    current_workflow_name = workflow_name(example_name)
    run_id = example_run_id()
    with propagate_attributes(
        custom_identifier=custom_identifier,
        trace_group_identifier=current_workflow_name,
        metadata={
            "example": example_name,
            "example_set": EXAMPLE_SET,
            "example_run_id": run_id,
            "run_id": run_id,
            "scenario_id": custom_identifier,
            "workflow_name": current_workflow_name,
        },
    ):
        yield custom_identifier


def client_mode() -> str:
    if os.getenv("MISTRAL_USE_MOCKS", "").lower() in {"1", "true", "yes"}:
        return "deterministic-current-sdk"
    return "direct-mistral" if mistral_api_key() else "respan-gateway"


def content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for item in content:
            text = getattr(item, "text", None)
            if text is None and isinstance(item, dict):
                text = item.get("text") or item.get("content")
            chunks.append(str(text if text is not None else item))
        return "".join(chunks)
    return str(content)


def root_request(example_name: str, prompt: str, **details: Any) -> dict[str, Any]:
    """Build bounded, JSON-native input for a decorated workflow boundary."""
    return {
        "scenario": example_name,
        "model": model_name(),
        "prompt": prompt,
        **details,
    }


def print_start(
    example_name: str, custom_identifier: str, mode: str | None = None
) -> None:
    print(f"example_run_id={example_run_id()}", flush=True)
    print(f"example={example_name}", flush=True)
    print(f"workflow_name={workflow_name(example_name)}", flush=True)
    print(f"custom_identifier={custom_identifier}", flush=True)
    print(f"client_mode={mode or client_mode()}", flush=True)


def print_result(
    example_name: str,
    custom_identifier: str,
    result: Any,
    mode: str | None = None,
) -> None:
    print(f"example={example_name}")
    print(f"example_run_id={example_run_id()}")
    print(f"workflow_name={workflow_name(example_name)}")
    print(f"custom_identifier={custom_identifier}")
    print(f"client_mode={mode or client_mode()}")
    print(f"model={model_name()}")
    if isinstance(result, str):
        print(result.strip())
    else:
        print(json.dumps(result, default=str, indent=2, sort_keys=True))


def finish_respan(respan: Respan) -> None:
    try:
        respan.flush()
    finally:
        respan.shutdown()
