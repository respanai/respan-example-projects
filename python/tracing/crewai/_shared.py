"""Shared helpers for the CrewAI Respan examples."""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from dotenv import load_dotenv
from respan import Respan
from respan_instrumentation_crewai import CrewAIInstrumentor

# Disable CrewAI's independent product telemetry; Respan still owns this run's export.
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("CREWAI_DISABLE_TRACKING", "true")
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
_STORAGE = TemporaryDirectory(prefix="respan-crewai-examples-")
os.environ.setdefault("CREWAI_STORAGE_DIR", _STORAGE.name)

DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
DEFAULT_RUN_ID = datetime.now(timezone.utc).strftime("crewai-%Y%m%d-%H%M%S")
DEFAULT_CUSTOMER_IDENTIFIER = "crewai-example-user"


@dataclass(frozen=True)
class GatewaySettings:
    api_key: str
    base_url: str
    model: str
    provider: str
    llm_api_key: str

    @property
    def uses_gateway(self) -> bool:
        return self.provider == "respan-gateway"


@dataclass(frozen=True)
class ExampleContext:
    respan: Respan
    settings: GatewaySettings
    example_name: str
    workflow_name: str
    run_id: str


def load_gateway_settings() -> GatewaySettings:
    _load_env_files()
    api_key = _first_env("RESPAN_API_KEY", "RESPAN_GATEWAY_API_KEY")
    base_url = _first_env(
        "RESPAN_BASE_URL",
        "RESPAN_GATEWAY_BASE_URL",
        default=DEFAULT_RESPAN_BASE_URL,
    )

    provider = os.getenv("CREWAI_RESPAN_LLM_PROVIDER", "respan-gateway").lower()

    if provider == "respan-gateway":
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_BASE_URL"] = base_url
        return GatewaySettings(
            api_key=api_key,
            base_url=base_url,
            model=os.getenv(
                "CREWAI_RESPAN_MODEL", os.getenv("RESPAN_MODEL", "gpt-4o-mini")
            ),
            provider=provider,
            llm_api_key=api_key,
        )

    if provider == "anthropic":
        return GatewaySettings(
            api_key=api_key,
            base_url=base_url,
            model=os.getenv("CREWAI_ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
            provider=provider,
            llm_api_key=_first_env("ANTHROPIC_API_KEY"),
        )

    if provider == "openai":
        os.environ.pop("OPENAI_BASE_URL", None)
        llm_api_key = _first_env("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = llm_api_key
        return GatewaySettings(
            api_key=api_key,
            base_url=base_url,
            model=os.getenv("CREWAI_OPENAI_MODEL", "gpt-4o-mini"),
            provider=provider,
            llm_api_key=llm_api_key,
        )

    raise RuntimeError(
        "CREWAI_RESPAN_LLM_PROVIDER must be one of: respan-gateway, anthropic, openai"
    )


def create_respan(
    *,
    app_name: str,
    example_name: str,
    workflow_name: str,
    **kwargs: Any,
) -> ExampleContext:
    settings = load_gateway_settings()
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID", DEFAULT_RUN_ID)
    metadata = {
        "example_set": "crewai",
        "example_name": example_name,
        "example_run_id": run_id,
        "run_id": run_id,
        "workflow_name": workflow_name,
    }
    metadata.update(kwargs.pop("metadata", {}))

    respan = Respan(
        app_name=app_name,
        api_key=settings.api_key,
        base_url=settings.base_url,
        instrumentations=[CrewAIInstrumentor()],
        customer_identifier=os.getenv(
            "RESPAN_EXAMPLE_CUSTOMER_IDENTIFIER",
            DEFAULT_CUSTOMER_IDENTIFIER,
        ),
        metadata=metadata,
        environment=os.getenv("RESPAN_EXAMPLE_ENVIRONMENT", "examples"),
        is_batching_enabled=False,
        log_level=os.getenv("RESPAN_LOG_LEVEL", "WARNING"),
        **kwargs,
    )
    return ExampleContext(
        respan=respan,
        settings=settings,
        example_name=example_name,
        workflow_name=workflow_name,
        run_id=run_id,
    )


def build_llm(settings: GatewaySettings):
    if os.getenv("CREWAI_USE_LIVE_LLM", "").lower() not in {"1", "true", "yes"}:
        return _build_deterministic_llm(settings)

    from crewai import LLM

    if settings.uses_gateway:
        return LLM(
            model=settings.model,
            api_key=settings.llm_api_key,
            base_url=settings.base_url,
        )

    return LLM(
        model=settings.model,
        api_key=settings.llm_api_key,
    )


def _build_deterministic_llm(settings: GatewaySettings):
    """Run CrewAI's native OpenAI connector against local HTTP fixtures."""
    from _fixtures import FixtureServer

    return FixtureServer().llm()


def run_with_attributes(context: ExampleContext, fn):
    with context.respan.propagate_attributes(
        customer_identifier=os.getenv(
            "RESPAN_EXAMPLE_CUSTOMER_IDENTIFIER",
            DEFAULT_CUSTOMER_IDENTIFIER,
        ),
        thread_identifier=f"{context.workflow_name}-{context.run_id}",
        custom_identifier=f"{context.example_name}-{context.run_id}",
        group_identifier=f"crewai-{context.run_id}",
        metadata={
            "example_set": "crewai",
            "example_name": context.example_name,
            "example_run_id": context.run_id,
            "run_id": context.run_id,
            "workflow_name": context.workflow_name,
        },
    ):
        return fn()


def result_text(result: object) -> str:
    raw = getattr(result, "raw", None)
    if raw:
        return str(raw)
    return str(result)


def print_result(label: str, value: object) -> None:
    print(f"{label}: {value}")


def _first_env(*names: str, default: str | None = None) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    if default is not None:
        return default
    joined = ", ".join(names)
    raise RuntimeError(f"Missing one of {joined} in the repo-root .env")


def _load_env_files() -> None:
    for env_path in _env_paths_from(start=Path(__file__).resolve().parent):
        load_dotenv(env_path, override=False)
    for env_path in _env_paths_from(start=Path.cwd()):
        load_dotenv(env_path, override=False)


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


def shutdown_respan(context: ExampleContext) -> None:
    from crewai.events.event_bus import crewai_event_bus

    try:
        if not crewai_event_bus.flush():
            raise RuntimeError("CrewAI event handlers did not finish before shutdown")
    finally:
        context.respan.shutdown()
