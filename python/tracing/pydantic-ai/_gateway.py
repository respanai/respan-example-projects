"""Shared Respan gateway configuration for Pydantic AI examples."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.openai import OpenAIProvider
from respan import Respan
from respan_instrumentation_pydantic_ai import PydanticAIInstrumentor

load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)


@dataclass(frozen=True)
class GatewayConfig:
    respan_api_key: str
    respan_base_url: str
    gateway_base_url: str
    gateway_api_key: str
    openai_model: str


def load_gateway_config() -> GatewayConfig:
    respan_api_key = os.environ["RESPAN_API_KEY"]
    respan_base_url = os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api").rstrip(
        "/"
    )
    gateway_base_url = os.getenv("RESPAN_GATEWAY_BASE_URL", respan_base_url).rstrip("/")
    gateway_api_key = os.getenv("RESPAN_GATEWAY_API_KEY", respan_api_key)
    openai_model = (
        os.getenv("PYDANTIC_AI_GATEWAY_MODEL")
        or os.getenv("RESPAN_VERTEX_GATEWAY_MODEL")
        or os.getenv("RESPAN_MODEL", "gpt-4o-mini")
    )

    os.environ["OPENAI_BASE_URL"] = gateway_base_url
    os.environ["OPENAI_API_KEY"] = gateway_api_key

    return GatewayConfig(
        respan_api_key=respan_api_key,
        respan_base_url=respan_base_url,
        gateway_base_url=gateway_base_url,
        gateway_api_key=gateway_api_key,
        openai_model=openai_model,
    )


def build_openai_chat_model(
    config: GatewayConfig | None = None,
    model_name: str | None = None,
) -> Model:
    config = config or load_gateway_config()
    if os.getenv("RESPAN_PYDANTIC_LIVE", "").lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return TestModel(model_name="test")
    return OpenAIChatModel(
        model_name or config.openai_model,
        provider=OpenAIProvider(
            base_url=config.gateway_base_url,
            api_key=config.gateway_api_key,
        ),
    )


def example_run_id() -> str:
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID")
    if marker:
        return marker
    marker = "otel2-pydantic-ai-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    os.environ["RESPAN_EXAMPLE_RUN_ID"] = marker
    return marker


def make_respan(
    example_name: str,
    *,
    include_content: bool = True,
    include_binary_content: bool = True,
    version: int = 5,
) -> Respan:
    marker = example_run_id()
    return Respan(
        app_name=f"pydantic-ai-{example_name}",
        api_key=config.respan_api_key if (config := load_gateway_config()) else "",
        base_url=config.respan_base_url,
        instrumentations=[
            PydanticAIInstrumentor(
                include_content=include_content,
                include_binary_content=include_binary_content,
                version=version,
            )
        ],
        metadata={
            "example_run_id": marker,
            "run_id": marker,
            "example_set": "pydantic-ai",
            "example_name": example_name,
        },
    )


def finish_respan(respan: Respan | None) -> None:
    if respan is None:
        return
    try:
        respan.flush()
    finally:
        respan.shutdown()
