"""Local recording by default; explicit export uses the released Respan exporter."""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from _scenarios import SCENARIOS
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan_instrumentation_anthropic import AnthropicInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE, RESPAN_METADATA


class MarkerProcessor(SpanProcessor):
    def __init__(self, marker: str, case: str):
        self.marker = json.dumps(
            {"run_id": marker, "integration": "anthropic", "case": case}
        )

    def on_start(self, span, parent_context=None):
        span.set_attribute(RESPAN_METADATA, self.marker)


def run_example(case: str) -> None:
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID", f"anthropic-{uuid4().hex}")
    provider = TracerProvider()
    provider.add_span_processor(MarkerProcessor(marker, case))
    local = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(local))
    wire = []
    statuses = []
    if os.getenv("RESPAN_EXAMPLE_EXPORT") == "1":
        from dotenv import load_dotenv
        from respan_tracing.exporters.respan import RespanSpanExporter

        load_dotenv(
            Path(
                os.getenv(
                    "RESPAN_EXAMPLE_ENV_FILE",
                    Path(__file__).resolve().parents[3] / ".env",
                )
            ),
            override=False,
        )
        key = os.getenv("RESPAN_API_KEY") or os.getenv("RESPAN_GATEWAY_API_KEY")
        if not key:
            raise RuntimeError("Set RESPAN_API_KEY to export controlled traces")
        remote = RespanSpanExporter(
            endpoint="https://api.respan.ai/api/v2/traces", api_key=key
        )
        original_post = remote._session.post

        def post(*args, **kwargs):
            # Observe the exporter's real body at its actual HTTP boundary.
            body = json.loads(kwargs["data"])
            result = original_post(*args, **kwargs)
            wire.append(body)
            statuses.append(result.status_code)
            return result

        remote._session.post = post
        provider.add_span_processor(SimpleSpanProcessor(remote))
    instrumentor = AnthropicInstrumentor(tracer_provider=provider)
    instrumentor.activate()
    try:
        with provider.get_tracer("anthropic_examples").start_as_current_span(
            f"anthropic_{case}", attributes={RESPAN_LOG_TYPE: "workflow"}
        ):
            result = SCENARIOS[case](provider)
    finally:
        instrumentor.deactivate()
        provider.force_flush()
        provider.shutdown()
    spans = [
        {
            "name": s.name,
            "trace_id": format(s.context.trace_id, "032x"),
            "span_id": format(s.context.span_id, "016x"),
            "parent_id": format(s.parent.span_id, "016x") if s.parent else None,
            "attributes": dict(s.attributes),
            "status": s.status.status_code.name,
            "description": s.status.description,
        }
        for s in local.get_finished_spans()
    ]
    if case == "privacy":
        calls = [span for span in spans if span["name"] == "anthropic.chat"]
        assert len(calls) == 4
        assert all(
            "traceloop.entity.input" not in span["attributes"]
            and "traceloop.entity.output" not in span["attributes"]
            and span["description"] is None
            for span in calls
        )
    evidence = {
        "run_id": marker,
        "case": case,
        "result": result,
        "spans": spans,
        "actual_exporter_bodies": wire,
        "http_statuses": statuses,
    }
    output = os.getenv("RESPAN_EXAMPLE_OUTPUT_DIR")
    if output:
        directory = Path(output)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{case}.json").write_text(json.dumps(evidence, indent=2))
    if wire and not statuses or any(status != 200 for status in statuses):
        raise AssertionError("Controlled export was not accepted by HTTP")
    print(
        json.dumps(
            {
                "case": case,
                "run_id": marker,
                "result": result,
                "local_span_count": len(spans),
                "export_body_count": len(wire),
                "http_statuses": statuses,
            }
        )
    )
