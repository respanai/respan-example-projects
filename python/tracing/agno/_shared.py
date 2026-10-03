"""Shared helpers for the Agno Respan examples."""

from __future__ import annotations

import os
from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
from respan import Respan
from respan_instrumentation_agno import AgnoInstrumentor


@dataclass(frozen=True)
class GatewaySettings:
    api_key: str
    base_url: str
    model: str


_DEFAULT_EXAMPLE_RUN_ID = f"agno-{uuid4().hex[:8]}"


def load_gateway_settings() -> GatewaySettings:
    _load_env_files()
    api_key = os.environ["RESPAN_API_KEY"]
    base_url = os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api")
    if not use_fixtures():
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_BASE_URL"] = base_url
    return GatewaySettings(
        api_key=api_key,
        base_url=base_url,
        model=os.getenv("RESPAN_MODEL", "gpt-4o-mini"),
    )


def create_respan(*, app_name: str, **kwargs) -> tuple[Respan, GatewaySettings]:
    settings = load_gateway_settings()
    run_id = example_run_id()
    metadata = {
        "integration": "agno",
        "run_id": run_id,
        **kwargs.pop("metadata", {}),
    }
    respan = Respan(
        app_name=app_name,
        api_key=settings.api_key,
        base_url=settings.base_url,
        instrumentations=[AgnoInstrumentor()],
        metadata=metadata,
        **kwargs,
    )
    return respan, settings


def example_run_id() -> str:
    return os.getenv("RESPAN_EXAMPLE_RUN_ID") or _DEFAULT_EXAMPLE_RUN_ID


@contextmanager
def example_attributes(respan: Respan, example_name: str):
    run_id = example_run_id()
    with respan.propagate_attributes(
        custom_identifier=f"{example_name}-{run_id}",
        trace_group_identifier=example_name,
        metadata={
            "integration": "agno",
            "example": example_name,
            "run_id": run_id,
        },
    ):
        yield run_id


def build_agent(
    *,
    name: str,
    instructions: str | list[str] | None = None,
    tools: list | None = None,
) -> Agent:
    return Agent(
        name=name,
        model=build_model(),
        instructions=instructions,
        tools=tools,
        telemetry=False,
    )


def use_fixtures() -> bool:
    return os.getenv("AGNO_USE_FIXTURES", "").lower() in {"1", "true", "yes"}


def build_model(model_class=OpenAIChat):
    if use_fixtures():
        from _fixture_model import model

        return model(model_class=model_class)
    return model_class(id=load_gateway_settings().model)


def print_result(label: str, value: object) -> None:
    print(f"{label}: {value}")


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
