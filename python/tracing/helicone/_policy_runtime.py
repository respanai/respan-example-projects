"""Native Helicone transport fixtures for the separate policy example runner."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
from pathlib import Path
from typing import Any

MODES = (
    "features",
    "drop",
    "record_only",
    "suppression",
    "capture_false",
    "environment_false",
    "context_false",
    "private_ancestor",
    "runtime_disabled",
    "delayed_policy",
    "delayed_parent",
    "lifecycle",
)

PRIVATE_MARKER = "helicone-policy-private-fixture"


class LocalReceiver:
    """Accept only synthetic Helicone logs and the local public OTLP pipeline."""

    def __init__(self) -> None:
        self.native_bodies: list[dict[str, Any]] = []
        self.otlp_bodies: list[dict[str, Any]] = []
        receiver = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                body = json.loads(
                    self.rfile.read(int(self.headers.get("Content-Length", "0")))
                )
                if self.path.startswith("/native/"):
                    receiver.native_bodies.append(body)
                elif self.path == "/api/v2/traces":
                    receiver.otlp_bodies.append(body)
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b"{}")

            def log_message(self, format: str, *args: Any) -> None:
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def run_case(mode: str) -> dict[str, Any]:
    # Do not load repository .env files. External export is explicit, and the
    # root audit runner supplies its configured endpoint and key only then.
    external = os.getenv("RESPAN_EXAMPLE_EXPORT") == "1"
    api_key = os.getenv("RESPAN_API_KEY") if external else "synthetic-respan-policy-key"
    base_url = os.getenv("RESPAN_BASE_URL") if external else None
    if external and (not api_key or not base_url):
        raise ValueError("Export requires RESPAN_API_KEY and RESPAN_BASE_URL")
    os.environ["OTEL_TRACES_SAMPLER"] = "always_off" if mode == "drop" else "always_on"
    os.environ["TRACELOOP_TRACE_CONTENT"] = (
        "false" if mode == "environment_false" else "true"
    )
    os.environ["NO_PROXY"] = ",".join(
        filter(None, (os.getenv("NO_PROXY"), "127.0.0.1", "localhost"))
    )

    from helicone_helpers import HeliconeManualLogger
    from helicone_helpers.manual_logger import LoggingOptions
    from opentelemetry import context, trace
    from opentelemetry.context import _SUPPRESS_INSTRUMENTATION_KEY
    from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )
    from opentelemetry.sdk.trace.sampling import (
        ALWAYS_OFF,
        ALWAYS_ON,
        Decision,
        ParentBased,
        Sampler,
        SamplingResult,
    )
    from opentelemetry.semconv_ai import SpanAttributes
    from opentelemetry.trace import StatusCode
    from respan import Respan, task, workflow
    from respan_instrumentation_helicone import HeliconeInstrumentor
    from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE
    from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY

    class RecordOnlySampler(Sampler):
        def should_sample(self, *_args: Any, **_kwargs: Any) -> SamplingResult:
            return SamplingResult(Decision.RECORD_ONLY)

        def get_description(self) -> str:
            return "HeliconeExampleRecordOnly"

    class EndObserver(SpanProcessor):
        def __init__(self) -> None:
            self.spans: list[Any] = []

        def on_start(self, span: Any, parent_context: Any = None) -> None:
            return

        def on_end(self, span: Any) -> None:
            self.spans.append(span)

        def shutdown(self) -> None:
            return

        def force_flush(self, timeout_millis: int = 30000) -> bool:
            return True

    @contextmanager
    def policy_value(key: str, value: Any):
        token = context.attach(context.set_value(key, value))
        try:
            yield
        finally:
            context.detach(token)

    receiver = LocalReceiver()
    instrumentor = HeliconeInstrumentor(capture_content=mode != "capture_false")
    runtime = Respan(
        api_key=api_key,
        base_url=base_url or receiver.base_url + "/api",
        app_name="helicone-policy-examples",
        instrumentations=[instrumentor],
        is_auto_instrument=False,
        is_enabled=mode != "runtime_disabled",
        is_batching_enabled=False,
        auto_flush="off",
        log_level="ERROR",
        metadata={
            "run_id": os.getenv("RESPAN_EXAMPLE_RUN_ID", "local"),
            "policy_case": mode,
        },
    )
    memory = InMemorySpanExporter()
    observer = EndObserver()
    provider: TracerProvider | None = None
    if mode != "runtime_disabled":
        runtime.telemetry.add_processor(exporter=memory, is_batching_enabled=False)
        active_provider = trace.get_tracer_provider()
        assert isinstance(active_provider, TracerProvider)
        provider = active_provider
        provider.add_span_processor(observer)
        if mode == "record_only":
            # Use the SDK's real sampler field, not a fabricated ReadableSpan.
            # Respan has already registered this sole provider and its processors.
            provider.sampler = RecordOnlySampler()
    native = HeliconeManualLogger(
        api_key="synthetic-helicone-policy-key",
        logging_endpoint=receiver.base_url + "/native",
        headers={"Helicone-Property-policy-case": mode},
    )
    native_results = []
    expected_native_times: dict[str, tuple[int, int]] = {}

    def request(model: str = "policy-model") -> dict[str, Any]:
        return {
            "model": model,
            "messages": [{"role": "user", "content": PRIVATE_MARKER}],
        }

    def response(model: str = "policy-model") -> dict[str, Any]:
        return {
            "model": model,
            "choices": [{"message": {"role": "assistant", "content": PRIVATE_MARKER}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        }

    def log_chat() -> None:
        application_result = object()

        def operation(recorder: Any) -> object:
            recorder.append_results(response())
            return application_result

        result = native.log_request(request(), operation, provider="openai")
        assert result is application_result
        native_results.append("original application result")

    async def send_builder(builder: Any) -> None:
        assert type(builder).__module__ == "helicone_helpers.manual_logger"
        assert await builder.send_log() is None
        native_results.append("original builder object and result")

    def make_builder() -> Any:
        builder = native.log_builder(request())
        builder.add_response(response())
        return builder

    def operation_error() -> None:
        failure = ValueError(PRIVATE_MARKER + " controlled operation error")

        def fail(_recorder: Any) -> None:
            raise failure

        try:
            native.log_request(request("policy-error-model"), fail, provider="openai")
        except ValueError as caught:
            assert caught is failure
            native_results.append("original operation exception")
        else:
            raise AssertionError("Helicone changed the operation exception")

    def basic_policy() -> None:
        log_chat()
        asyncio.run(send_builder(make_builder()))
        operation_error()

    def features() -> None:
        native_start = time.time()
        time.sleep(0.012)
        native_end = time.time()
        options: LoggingOptions = {"start_time": native_start, "end_time": native_end}
        expected_native_times["manual"] = (
            int(native_start * 1_000_000_000),
            int(native_end * 1_000_000_000),
        )
        large_request = request("policy-feature-model")
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": f"{PRIVATE_MARKER}-{index}"}
            for index in range(80)
        ]
        messages[0]["content"] = [
            {"type": "text", "text": PRIVATE_MARKER},
            {
                "type": "image_url",
                "image_url": {"url": "data:image/png;base64,c3ludGhldGlj"},
            },
        ]
        large_request["messages"] = messages
        large_request["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": f"policy_tool_{index}",
                    "parameters": {"type": "object"},
                },
            }
            for index in range(75)
        ]
        large_response = response("policy-feature-model")
        large_response["choices"][0]["message"]["tool_calls"] = [
            {
                "id": "policy-native-call",
                "type": "function",
                "function": {"name": "policy_tool_0", "arguments": '{"value":7}'},
            }
        ]
        native.send_log(
            "openai",
            large_request,
            large_response,
            options,
        )
        native.send_log(
            None,
            {
                "_type": "tool",
                "toolName": "policy_lookup",
                "input": {"query": PRIVATE_MARKER},
            },
            {"result": PRIVATE_MARKER},
            options,
        )
        native.send_log(
            "openai",
            {
                "_type": "embedding",
                "model": "policy-embedding-model",
                "input": [PRIVATE_MARKER],
            },
            {
                "data": [{"embedding": [index / 5001 for index in range(5001)]}],
                "usage": {"prompt_tokens": 3, "total_tokens": 3},
            },
            options,
        )
        stream = native.log_builder(request("policy-stream-model"))
        stream.add_chunk(
            {
                "model": "policy-stream-model",
                "choices": [{"delta": {"content": "first "}}],
            }
        )
        stream.add_chunk(
            {
                "choices": [{"delta": {"content": "last"}}],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 2,
                    "total_tokens": 2,
                },
            }
        )
        asyncio.run(send_builder(stream))
        expected_native_times["policy-stream-model"] = (
            # Builder creation stores milliseconds; the terminal native send
            # supplies seconds. Convert each original value in its own unit.
            int(stream.start_time * 1_000_000),
            int(stream.end_time / 1000 * 1_000_000_000),
        )
        failed = native.new_builder(request("policy-builder-error-model"))
        failed.set_error(RuntimeError("controlled builder error"))
        asyncio.run(send_builder(failed))
        expected_native_times["policy-builder-error-model"] = (
            int(failed.start_time * 1_000_000),
            int(failed.end_time / 1000 * 1_000_000_000),
        )
        operation_error()

    def private_boundary(action: Callable[[], None]) -> None:
        @task(name="helicone-private-policy-boundary")
        def private_task() -> None:
            trace.get_current_span().set_attribute("allow_trace_content", False)
            with policy_value(ENABLE_CONTENT_TRACING_KEY, True):
                action()

        private_task()

    @workflow(name="helicone-policy-" + mode)
    def workflow_case() -> None:
        if mode == "features":
            features()
        elif mode == "suppression":
            with policy_value(_SUPPRESS_INSTRUMENTATION_KEY, True):
                basic_policy()
                created_suppressed = make_builder()
            asyncio.run(send_builder(created_suppressed))
            created_enabled = make_builder()
            with policy_value(_SUPPRESS_INSTRUMENTATION_KEY, True):
                asyncio.run(send_builder(created_enabled))
        elif mode in {"capture_false", "environment_false"}:
            with policy_value(ENABLE_CONTENT_TRACING_KEY, True):
                basic_policy()
        elif mode == "context_false":
            with policy_value(ENABLE_CONTENT_TRACING_KEY, False):
                basic_policy()
        elif mode == "private_ancestor":

            def operation(recorder: Any) -> None:
                trace.get_current_span().set_attribute("allow_trace_content", False)
                with policy_value(ENABLE_CONTENT_TRACING_KEY, True):
                    log_chat()
                recorder.append_results(response())

            native.log_request(request(), operation, provider="openai")
        elif mode == "delayed_policy":
            with policy_value(ENABLE_CONTENT_TRACING_KEY, False):
                builder = make_builder()
            with policy_value(ENABLE_CONTENT_TRACING_KEY, True):
                asyncio.run(send_builder(builder))
            admitted = make_builder()
            private_boundary(lambda: asyncio.run(send_builder(admitted)))
            mutated_private = native.log_builder(request())
            private_boundary(lambda: mutated_private.add_response(response()))
            asyncio.run(send_builder(mutated_private))
        elif mode == "delayed_parent":
            assert provider is not None
            provider.sampler = ALWAYS_OFF
            try:
                with trace.get_tracer("helicone-policy-example").start_as_current_span(
                    "dropped-builder-owner"
                ):
                    created_dropped = make_builder()
            finally:
                # ParentBased must use the captured dropped parent rather than
                # the currently sampled workflow when the builder is sent.
                provider.sampler = ParentBased(root=ALWAYS_ON)
            asyncio.run(send_builder(created_dropped))
        elif mode == "lifecycle":
            stale = make_builder()
            instrumentor.deactivate()
            instrumentor.activate()
            asyncio.run(send_builder(stale))
            asyncio.run(send_builder(make_builder()))
        else:
            basic_policy()

    try:
        if mode == "record_only":
            log_chat()
        else:
            workflow_case()
        runtime.flush()
        spans: list[Any] = list(memory.get_finished_spans())
        native_spans = [
            span
            for span in spans
            if span.instrumentation_scope.name == "respan.instrumentation.helicone"
        ]
        observed_native = [
            span
            for span in observer.spans
            if span.instrumentation_scope.name == "respan.instrumentation.helicone"
        ]
        expected_native = {
            "features": 6,
            "drop": 0,
            "record_only": 0,
            "suppression": 0,
            "capture_false": 3,
            "environment_false": 3,
            "context_false": 3,
            "private_ancestor": 2,
            "runtime_disabled": 0,
            "delayed_policy": 3,
            "delayed_parent": 0,
            "lifecycle": 1,
        }[mode]
        expected_root = 0 if mode in {"drop", "record_only", "runtime_disabled"} else 1
        if mode == "delayed_policy":
            expected_root += 2
        assert len(native_spans) == expected_native, (
            mode,
            len(native_spans),
            expected_native,
        )
        assert len(spans) == expected_native + expected_root, (
            mode,
            [
                (
                    span.name,
                    span.attributes.get(RESPAN_LOG_TYPE),
                    span.instrumentation_scope.name,
                )
                for span in spans
            ],
        )
        if mode == "record_only":
            assert len(observed_native) == 1
            assert observed_native[0].context.trace_flags.sampled is False
            assert PRIVATE_MARKER not in json.dumps(dict(observed_native[0].attributes))
        if mode in {
            "capture_false",
            "environment_false",
            "context_false",
            "private_ancestor",
            "delayed_policy",
        }:
            for span in native_spans:
                native_content = {
                    "attributes": dict(span.attributes),
                    "status_description": span.status.description,
                    "events": [dict(event.attributes or {}) for event in span.events],
                }
                assert PRIVATE_MARKER not in json.dumps(native_content), mode
                assert span.status.description is None, mode
            assert all(
                span.attributes.get(SpanAttributes.LLM_REQUEST_MODEL)
                for span in native_spans
            )
        if mode == "features":
            for span in native_spans[:3]:
                assert (span.start_time, span.end_time) == expected_native_times[
                    "manual"
                ]
                assert span.end_time > span.start_time
            for span in native_spans:
                model = span.attributes.get(SpanAttributes.LLM_REQUEST_MODEL)
                if model in expected_native_times:
                    assert (span.start_time, span.end_time) == expected_native_times[
                        model
                    ], (
                        model,
                        (span.start_time, span.end_time),
                        expected_native_times[model],
                    )
                    assert span.end_time > span.start_time
            chat = next(
                span
                for span in native_spans
                if span.attributes.get(SpanAttributes.LLM_REQUEST_MODEL)
                == "policy-feature-model"
            )
            captured_request = json.loads(
                chat.attributes[SpanAttributes.TRACELOOP_ENTITY_INPUT]
            )
            assert len(captured_request["messages"]) == 80
            assert captured_request["messages"][-1]["content"] == f"{PRIVATE_MARKER}-79"
            assert captured_request["messages"][0]["content"][1]["type"] == "image_url"
            assert (
                len(json.loads(chat.attributes[SpanAttributes.LLM_REQUEST_FUNCTIONS]))
                == 75
            )
            assert (
                json.loads(
                    chat.attributes[f"{SpanAttributes.LLM_COMPLETIONS}.0.tool_calls"]
                )[0]["id"]
                == "policy-native-call"
            )
            vector = next(
                span
                for span in native_spans
                if span.attributes.get(RESPAN_LOG_TYPE) == "embedding"
            )
            vector_output = json.loads(
                vector.attributes[SpanAttributes.TRACELOOP_ENTITY_OUTPUT]
            )
            assert len(vector_output) == 5001
            assert vector_output[0] == 0
            assert vector_output[-1] == 5000 / 5001
            stream = next(
                span
                for span in native_spans
                if span.attributes.get(SpanAttributes.LLM_REQUEST_MODEL)
                == "policy-stream-model"
            )
            assert (
                stream.attributes[f"{SpanAttributes.LLM_COMPLETIONS}.0.content"]
                == "first last"
            )
            assert stream.attributes[SpanAttributes.LLM_USAGE_PROMPT_TOKENS] == 0
            assert (
                sum(
                    span.status.status_code == StatusCode.ERROR for span in native_spans
                )
                == 2
            )
        if not external:
            wire_spans = [
                span
                for body in receiver.otlp_bodies
                for resource in body.get("resourceSpans", [])
                for scope in resource.get("scopeSpans", [])
                for span in scope.get("spans", [])
            ]
            assert len(wire_spans) == len(spans), (mode, len(wire_spans), len(spans))
            if mode in {
                "capture_false",
                "environment_false",
                "context_false",
                "private_ancestor",
                "delayed_policy",
            }:
                for span in native_spans:
                    matches = [
                        wire
                        for wire in wire_spans
                        if wire.get("spanId") == f"{span.context.span_id:016x}"
                    ]
                    assert len(matches) == 1
                    assert PRIVATE_MARKER not in json.dumps(matches[0]), mode
        summary = {
            "mode": mode,
            "exported_spans": len(spans),
            "native_spans": len(native_spans),
            "native_http_posts": len(receiver.native_bodies),
            "native_results_preserved": len(native_results),
            "observed_record_only_spans": len(observed_native)
            if mode == "record_only"
            else 0,
            "external_export": external,
            "native_timing_assertions": len(expected_native_times),
            "versions": {
                name: version(name)
                for name in (
                    "helicone-helpers",
                    "respan-ai",
                    "respan-tracing",
                    "respan-sdk",
                    "respan-instrumentation-helicone",
                    "opentelemetry-sdk",
                )
            },
            "spans": [
                {
                    "name": span.name,
                    "trace_id": f"{span.context.trace_id:032x}",
                    "span_id": f"{span.context.span_id:016x}",
                    "parent_id": f"{span.parent.span_id:016x}" if span.parent else None,
                    "sampled": span.context.trace_flags.sampled,
                    "log_type": span.attributes.get(RESPAN_LOG_TYPE),
                    "status": span.status.status_code.name,
                }
                for span in spans
            ],
        }
        capture_path = os.getenv("RESPAN_EXAMPLE_CAPTURE_PATH")
        if capture_path:
            Path(capture_path).mkdir(parents=True, exist_ok=True)
            Path(capture_path, mode + ".json").write_text(
                json.dumps(
                    {"summary": summary, "local_wire": receiver.otlp_bodies}, indent=2
                )
                + "\n"
            )
        return summary
    finally:
        runtime.shutdown()
        receiver.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=MODES)
    print(json.dumps(run_case(parser.parse_args().mode), sort_keys=True))
