"""Shared helpers for the Semantic Kernel Respan examples."""

from __future__ import annotations

import os
from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from respan import Respan, propagate_attributes
from respan_instrumentation_semantic_kernel import SemanticKernelInstrumentor
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

DEFAULT_RUN_ID = datetime.now(timezone.utc).strftime("semantic-kernel-%Y%m%d-%H%M%S")
_CLIENTS: list[AsyncOpenAI] = []


@dataclass(frozen=True)
class GatewaySettings:
    api_key: str
    base_url: str
    model: str


def load_repo_env() -> None:
    """Load environment variables from respan-example-projects/.env."""
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env", override=False)


def example_run_id() -> str:
    load_repo_env()
    return os.getenv("RESPAN_EXAMPLE_RUN_ID", DEFAULT_RUN_ID)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be set in respan-example-projects/.env")
    return value


def gateway_settings() -> GatewaySettings:
    load_repo_env()
    api_key = os.getenv("RESPAN_GATEWAY_API_KEY") or require_env("RESPAN_API_KEY")
    base_url = os.getenv(
        "RESPAN_GATEWAY_BASE_URL",
        os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
    )
    return GatewaySettings(
        api_key=api_key,
        base_url=base_url,
        model=os.getenv("RESPAN_MODEL", "gpt-4o-mini"),
    )


def create_respan(app_name: str, *, capture_content: bool = True) -> Respan:
    load_repo_env()
    run_id = example_run_id()
    return Respan(
        app_name=app_name,
        api_key=require_env("RESPAN_API_KEY"),
        base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
        instrumentations=[SemanticKernelInstrumentor(capture_content=capture_content)],
        is_batching_enabled=False,
        metadata={
            "integration": "semantic-kernel",
            "example_set": "semantic-kernel",
            "example": app_name,
            "run_id": run_id,
            "example_run_id": run_id,
        },
        environment="examples",
    )


def create_kernel(*, with_chat_service: bool = True) -> Kernel:
    kernel = Kernel()
    if not with_chat_service:
        return kernel

    client = create_client(allow_live=True)
    settings = (
        gateway_settings()
        if live_enabled()
        else GatewaySettings(
            "fixture-only", "https://fixture.invalid/v1", "fixture-model"
        )
    )
    kernel.add_service(
        OpenAIChatCompletion(
            ai_model_id=settings.model,
            service_id="chat",
            async_client=client,
        )
    )
    return kernel


def live_enabled() -> bool:
    return os.getenv("SEMANTIC_KERNEL_LIVE") == "1"


def create_client(*, allow_live: bool = False) -> AsyncOpenAI:
    if allow_live and live_enabled():
        settings = gateway_settings()
        client = AsyncOpenAI(
            api_key=settings.api_key, base_url=settings.base_url, max_retries=0
        )
    else:
        from _fixtures import FixtureServer

        client = FixtureServer().client()
    _CLIENTS.append(client)
    return client


async def close_kernel_clients() -> None:
    while _CLIENTS:
        client = _CLIENTS.pop()
        await client.close()


@contextmanager
def example_attributes(app_name: str):
    run_id = example_run_id()
    with propagate_attributes(
        trace_group_identifier=app_name,
        metadata={
            "integration": "semantic-kernel",
            "example_set": "semantic-kernel",
            "example": app_name,
            "run_id": run_id,
            "example_run_id": run_id,
        },
    ):
        yield


def print_result(label: str, value: object) -> None:
    print(f"{label}: {value}")


def _env_paths_from(*, start: Path) -> Iterable[Path]:
    current = start.resolve()
    chain: list[Path] = []
    while True:
        chain.append(current)
        if (current / ".git").exists():
            break
        if current.parent == current:
            break
        current = current.parent

    seen: set[Path] = set()
    for directory in reversed(chain):
        env_path = directory / ".env"
        if env_path.exists() and env_path not in seen:
            seen.add(env_path)
            yield env_path
