"""Native SDK fixtures by default, with separately enabled trace export/live calls."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import httpx
from _fixture import Transport
from dotenv import load_dotenv
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from portkey_ai import AsyncPortkey, Portkey
from respan import Respan, propagate_attributes
from respan_instrumentation_portkey import PortkeyInstrumentor

EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parents[2]
DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
DEFAULT_MODEL = "gpt-4.1-nano"


def load_root_env():
    load_dotenv(REPO_ROOT / ".env", override=False)


def marker():
    return (
        os.getenv("RESPAN_EXAMPLE_RUN_ID", "").strip() or "portkey-" + uuid4().hex[:10]
    )


def execution_id():
    return uuid4().hex[:10]


def workflow_name(example_name):
    return "portkey_" + example_name.replace("-", "_")


def make_respan(example_name, run_marker, *, capture_content=True):
    exporting = os.getenv("RESPAN_PORTKEY_EXPORT") == "1"
    if exporting:
        load_root_env()
        if not os.getenv("RESPAN_API_KEY"):
            raise RuntimeError("RESPAN_API_KEY required for explicit export")
    previous = os.environ.pop("RESPAN_API_KEY", None) if not exporting else None
    try:
        respan = Respan(
            api_key=os.getenv("RESPAN_API_KEY") if exporting else None,
            base_url=os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL),
            app_name=workflow_name(example_name),
            instrumentations=[PortkeyInstrumentor(capture_content=capture_content)],
            metadata={
                "example_set": "portkey",
                "run_id": run_marker,
                "example_run_id": run_marker,
                "workflow_name": workflow_name(example_name),
            },
            log_level="WARNING",
        )
    finally:
        if previous is not None:
            os.environ["RESPAN_API_KEY"] = previous
    if not exporting:
        respan.telemetry.add_processor(exporter=InMemorySpanExporter())
    return respan


def live_configured():
    return os.getenv("RESPAN_PORTKEY_LIVE") == "1" and bool(
        os.getenv("PORTKEY_API_KEY")
    )


def _client_kwargs(*, live, asynchronous=False):
    if live:
        load_root_env()
        if not live_configured():
            raise RuntimeError("RESPAN_PORTKEY_LIVE=1 and PORTKEY_API_KEY required")
        kwargs = {"api_key": os.environ["PORTKEY_API_KEY"]}
        for env, key in [
            ("PORTKEY_BASE_URL", "base_url"),
            ("PORTKEY_PROVIDER", "provider"),
            ("PORTKEY_CONFIG", "config"),
        ]:
            if os.getenv(env):
                kwargs[key] = os.environ[env]
        return kwargs
    url = "https://portkey.test"
    cls = httpx.AsyncClient if asynchronous else httpx.Client
    return {
        "api_key": "fixture",
        "base_url": url,
        "http_client": cls(base_url=url, transport=httpx.MockTransport(Transport())),
        "max_retries": 0,
    }


def make_client(*, live=False):
    return Portkey(**_client_kwargs(live=live))


def make_async_client(*, live=False):
    return AsyncPortkey(**_client_kwargs(live=live, asynchronous=True))


def model_name(*, live=False):
    return os.getenv("PORTKEY_MODEL", DEFAULT_MODEL) if live else "fixture-model"


@contextmanager
def example_attributes(example_name, run_marker, execution, *, mode):
    with propagate_attributes(
        metadata={
            "example_set": "portkey",
            "example": example_name,
            "run_id": run_marker,
            "example_run_id": run_marker,
            "execution_id": execution,
            "mode": mode,
        },
        trace_group_identifier=workflow_name(example_name) + "-" + run_marker,
    ):
        yield


def print_result(example_name, run_marker, result):
    print("RESPAN_EXAMPLE_RUN_ID=" + run_marker)
    print(example_name + ": " + json.dumps(result, allow_nan=False))


def finish_respan(respan):
    try:
        respan.flush()
    finally:
        respan.shutdown()
