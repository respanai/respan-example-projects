"""Superagent examples using controlled SDK boundaries by default."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class ExampleConfig:
    respan_api_key: str
    respan_base_url: str
    model: str


def configure_environment():
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID")
    load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)
    if marker is not None:
        os.environ["RESPAN_EXAMPLE_RUN_ID"] = marker
    return ExampleConfig(
        os.getenv("RESPAN_API_KEY", ""),
        os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
        "openai/gpt-4o-mini"
        if os.getenv("SUPERAGENT_EXAMPLE_MODE", "fixture") == "fixture"
        else os.getenv("SUPERAGENT_MODEL", "openai/gpt-4o-mini"),
    )


def create_respan(app_name="superagent-example"):
    from respan import Respan
    from respan_instrumentation_superagent import SuperagentInstrumentor

    config = configure_environment()
    if not config.respan_api_key:
        raise ValueError("Set RESPAN_API_KEY to export the example traces.")
    return Respan(
        api_key=config.respan_api_key,
        base_url=config.respan_base_url,
        app_name=app_name,
        instrumentations=[SuperagentInstrumentor()],
        metadata={
            "run_id": example_marker(),
            "integration": "superagent",
            "script": app_name,
        },
        is_batching_enabled=False,
    )


@contextmanager
def client_context(**kwargs):
    if os.getenv("SUPERAGENT_EXAMPLE_MODE", "fixture") == "fixture":
        from _fixtures import fixture_client

        with fixture_client(**kwargs) as (client, _):
            yield client
    else:
        from safety_agent import create_client

        yield create_client()


def example_marker():
    configure_environment()
    return os.getenv("RESPAN_EXAMPLE_RUN_ID", "superagent-local")


def finish_respan(respan):
    try:
        respan.flush()
    finally:
        respan.shutdown()
