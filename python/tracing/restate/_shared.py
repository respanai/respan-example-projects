"""Controlled native SDK invocation; trace export requires an explicit opt-in."""

from __future__ import annotations

import asyncio
import inspect
import json
import os
from contextlib import AsyncExitStack, contextmanager
from pathlib import Path

from dotenv import load_dotenv
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan import Respan, propagate_attributes
from respan_instrumentation_restate import RestateInstrumentor
from respan_tracing.exporters import RespanSpanExporter
from respan_tracing.exporters.respan import _span_to_otlp_json
from restate.handler import invoke_handler
from restate.server_context import (
    ServerInvocationContext,
    _restate_context_var,
    restate_context_is_replaying,
)
from restate.server_types import ReceiveChannel
from restate.vm import Invocation, VMWrapper

EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parents[2]
EXAMPLE_SET = "restate"


def run_id():
    return os.getenv("RESPAN_EXAMPLE_RUN_ID", "restate-local")


def create_respan(*, capture_content=True):
    export = os.getenv("RESPAN_EXAMPLE_EXPORT") == "1"
    if export:
        load_dotenv(REPO_ROOT / ".env", override=False)
    # The facade reads this environment credential. Suppress its default export
    # so local runs remain local even if the caller already has credentials.
    api_key = os.environ.pop("RESPAN_API_KEY", None)
    try:
        respan = Respan(
            api_key=None,
            app_name="restate-examples",
            metadata={
                "example_set": EXAMPLE_SET,
                "example_run_id": run_id(),
                "run_id": run_id(),
            },
            instrumentations=[RestateInstrumentor(capture_content=capture_content)],
            is_auto_instrument=False,
            is_batching_enabled=False,
            log_level="WARNING",
        )
    finally:
        if api_key is not None:
            os.environ["RESPAN_API_KEY"] = api_key
    respan.example_memory = InMemorySpanExporter()
    respan.telemetry.add_processor(respan.example_memory, is_batching_enabled=False)
    if export:
        if not api_key:
            raise RuntimeError("RESPAN_EXAMPLE_EXPORT=1 requires RESPAN_API_KEY")
        respan.telemetry.add_processor(
            RespanSpanExporter(
                endpoint="https://api.respan.ai/api/v2/traces", api_key=api_key
            ),
            is_batching_enabled=False,
        )
    return respan


@contextmanager
def example_context(case):
    with propagate_attributes(
        custom_identifier=f"{EXAMPLE_SET}-{case}-{run_id()}",
        trace_group_identifier=f"restate_{case}",
        metadata={
            "example_set": EXAMPLE_SET,
            "example_case": case,
            "example_run_id": run_id(),
            "run_id": run_id(),
        },
    ):
        yield


async def invoke_registered_handler(
    component,
    handler_name,
    payload,
    *,
    invocation_id,
    key=None,
    replaying=False,
    codec=None,
):
    """Run native serde and invoke_handler without a deployed Restate service.

    This fixture exercises the invocation-manager boundary. It does not emulate
    a journal, durable operations, network attempts, or production replay.
    """
    handler = component.handlers[handler_name]
    encoded = handler.handler_io.input_serde.serialize(payload)
    invocation = Invocation(
        invocation_id,
        7,
        [],
        encoded,
        key or "",
        "example-scope",
        "example-limit",
        "example-idempotency",
    )
    queue = asyncio.Queue()
    receive = ReceiveChannel(queue.get)

    async def send(event):
        pass

    native = ServerInvocationContext(
        VMWrapper([("content-type", "application/vnd.restate.invocation.v5")]),
        handler,
        invocation,
        {},
        send,
        receive,
        **(
            {"journal_codec": codec}
            if "journal_codec" in inspect.signature(ServerInvocationContext).parameters
            else {}
        ),
    )
    token = _restate_context_var.set(native)
    replay_token = restate_context_is_replaying.set(replaying)
    try:
        async with AsyncExitStack() as stack:
            for manager in handler.context_managers or ():
                await stack.enter_async_context(manager())
            output = await invoke_handler(
                handler,
                native,
                encoded,
                **(
                    {"journal_codec": codec}
                    if "journal_codec" in inspect.signature(invoke_handler).parameters
                    else {}
                ),
            )
            return json.loads(output) if output else None
    finally:
        restate_context_is_replaying.reset(replay_token)
        _restate_context_var.reset(token)
        await receive.close()


def finish_respan(respan):
    try:
        respan.flush()
        directory = os.getenv("RESPAN_EXAMPLE_REPORT_DIR")
        if directory:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            import sys

            (path / (Path(sys.argv[0]).stem + ".json")).write_text(
                json.dumps(
                    [
                        _span_to_otlp_json(span)
                        for span in respan.example_memory.get_finished_spans()
                    ],
                    indent=2,
                )
            )
    finally:
        respan.shutdown()
        respan.telemetry.tracer.tracer_provider.shutdown()
