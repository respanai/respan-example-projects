"""Shared helpers for MCP tracing examples."""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client import stdio
from respan import Respan
from respan_instrumentation_mcp import MCPInstrumentor

EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parents[2]
SERVER_SCRIPT = EXAMPLE_DIR / "server.py"
RESPAN_BASE_URL = "https://api.respan.ai/api"
EXAMPLE_SET = "mcp"


def load_example_env() -> None:
    load_dotenv(REPO_ROOT / ".env")
    if not os.getenv("RESPAN_API_KEY"):
        raise RuntimeError(f"RESPAN_API_KEY is required in {REPO_ROOT / '.env'}")
    os.environ.setdefault("RESPAN_BASE_URL", RESPAN_BASE_URL)


def create_respan(workflow_name: str) -> Respan:
    load_example_env()
    return Respan(
        api_key=os.environ["RESPAN_API_KEY"],
        base_url=os.getenv("RESPAN_BASE_URL", RESPAN_BASE_URL),
        app_name=workflow_name,
        metadata={"example_set": EXAMPLE_SET, "workflow_name": workflow_name},
        instrumentations=[MCPInstrumentor()],
        is_batching_enabled=False,
        log_level=os.getenv("RESPAN_LOG_LEVEL", "WARNING"),
    )


def workflow_attributes(workflow_name: str) -> dict[str, object]:
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID") or uuid4().hex[:8]
    invocation_id = uuid4().hex[:8]
    return {
        "trace_group_identifier": workflow_name,
        "custom_identifier": f"{run_id}:{workflow_name}",
        "metadata": {
            "example_set": EXAMPLE_SET,
            "workflow_name": workflow_name,
            "example_run_id": run_id,
            "run_id": run_id,
            "example_invocation_id": invocation_id,
        },
    }


@asynccontextmanager
async def with_session(*, server_args: tuple[str, ...] = ()):
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_SCRIPT), *server_args],
        cwd=str(EXAMPLE_DIR),
    )
    async with (
        stdio.stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        yield session


def finish_respan(respan: Respan) -> None:
    try:
        respan.flush()
    finally:
        respan.shutdown()


def print_result(workflow_name: str, result: Any) -> None:
    print(f"{workflow_name}: {result}", flush=True)
