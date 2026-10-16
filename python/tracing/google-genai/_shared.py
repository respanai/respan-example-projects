from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from google import genai
from respan import Respan, propagate_attributes
from respan_instrumentation_google_genai import GoogleGenAIInstrumentor

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
DEFAULT_MODEL = "gemini-3-flash-preview"


def load_root_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def require_respan_api_key() -> str:
    load_root_env()
    api_key = os.getenv("RESPAN_API_KEY")
    if not api_key:
        raise RuntimeError("RESPAN_API_KEY must be set in the repo root .env file")
    return api_key


def respan_base_url() -> str:
    return os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL).rstrip("/")


def google_gateway_base_url() -> str:
    base_url = respan_base_url()
    if base_url.endswith("/google/gemini"):
        return base_url
    return f"{base_url}/google/gemini"


def model_name() -> str:
    return os.getenv("RESPAN_GOOGLE_GENAI_MODEL", DEFAULT_MODEL)


def make_respan(example_name: str) -> Respan:
    api_key = require_respan_api_key()
    run_id = example_run_id()
    return Respan(
        api_key=api_key,
        base_url=respan_base_url(),
        app_name="google-genai-examples",
        instrumentations=[GoogleGenAIInstrumentor()],
        environment=os.getenv("RESPAN_ENVIRONMENT", "example"),
        metadata={
            "integration": "google-genai",
            "example": example_name,
            "run_id": run_id,
        },
    )


def google_api_key() -> str | None:
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


def make_client() -> genai.Client:
    if os.getenv("RESPAN_GOOGLE_GENAI_MODE") == "fixture":
        from _fixtures import make_fixture_client

        return make_fixture_client()
    direct_api_key = google_api_key()
    if direct_api_key:
        return genai.Client(api_key=direct_api_key)

    api_key = require_respan_api_key()
    return genai.Client(
        api_key=api_key,
        http_options={"base_url": google_gateway_base_url()},
    )


def workflow_name(example_name: str) -> str:
    normalized_name = example_name.replace("-", "_")
    return f"google_genai_{normalized_name}"


def make_custom_identifier(example_name: str) -> str:
    return f"{example_run_id()}:{example_name}"


def example_run_id() -> str:
    return os.getenv("RESPAN_EXAMPLE_RUN_ID") or f"google-genai-{uuid4().hex[:10]}"


@contextmanager
def example_attributes(example_name: str, custom_identifier: str | None = None):
    custom_identifier = custom_identifier or make_custom_identifier(example_name)
    current_workflow_name = workflow_name(example_name)
    with propagate_attributes(
        custom_identifier=custom_identifier,
        trace_group_identifier=current_workflow_name,
        metadata={
            "example": example_name,
            "integration": "google-genai",
            "run_id": example_run_id(),
            "workflow_name": current_workflow_name,
        },
    ):
        yield custom_identifier


def client_mode() -> str:
    if os.getenv("RESPAN_GOOGLE_GENAI_MODE") == "fixture":
        return "deterministic-sdk-http-fixture"
    return "direct-google" if google_api_key() else "respan-gateway"


def print_result(example_name: str, custom_identifier: str, text: str) -> None:
    print(f"example={example_name}")
    print(f"custom_identifier={custom_identifier}")
    print(f"client_mode={client_mode()}")
    print(text.strip())
