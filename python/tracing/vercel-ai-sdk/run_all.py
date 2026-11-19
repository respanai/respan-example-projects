"""Run released AI SDK scenarios and export their telemetry to Respan.

Install the local respan-instrumentation-vercel checkout before running.
The deterministic scenarios use the real SDK with its FakeModel/test provider;
--live additionally calls the configured Respan Gateway using RESPAN_API_KEY.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from importlib.metadata import version
from pathlib import Path

import ai
import ai.ops
import ai.testing
import pydantic
from ai import experimental_telemetry as telemetry
from ai.providers.base import Provider
from ai.providers.openai import OpenAIChatCompletionsProtocol
from ai.types.messages import FilePart
from ai.types.usage import Usage
from dotenv import load_dotenv
from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv_ai import SpanAttributes
from respan_instrumentation_vercel import VercelInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE, RESPAN_METADATA
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY
from respan_tracing.exporters.respan import RespanSpanExporter


class ExampleProvider(Provider):
    provider_class_id: str = "respan-vercel-example"
    name: str = "example"
    default_base_url: str = "https://example.invalid"

    async def embed(self, model, values, *, params):
        if values == ["expected error"]:
            raise ValueError("Expected embedding example failure")
        return ai.ops.Item(
            value=[[0.25, 0.75] for _ in values], usage=Usage(input_tokens=6)
        )

    async def generate_image(self, model, prompt, *, params):
        return ai.ops.Item(
            value=[FilePart(data=b"example-image", media_type="image/png")]
        )

    async def generate_video(self, model, prompt, *, params):
        return ai.ops.Item(
            value=[FilePart(data=b"example-video", media_type="video/mp4")]
        )

    async def generate_audio(self, model, prompt, *, params):
        return ai.ops.Item(
            value=[FilePart(data=b"example-audio", media_type="audio/wav")]
        )

    async def transcribe(self, model, audio, *, params):
        return ai.ops.Item(
            value=ai.ops.Transcription(text="hello from transcription", language="en")
        )

    async def rerank(self, model, documents, query, *, params):
        return ai.ops.Item(value=[ai.ops.RankedDocument(index=1, score=0.9)])

    async def evaluate(self, model, state, questions, *, params):
        return ai.ops.Item(value={"correct": {"noul": 0.95}})


async def text():
    prompt = ai.user_message("Reply with hello")
    response = ai.assistant_message("hello").model_copy(
        update={"usage": Usage(input_tokens=4, output_tokens=1)}
    )
    for streaming in (False, True):
        model = ai.testing.FakeModel([prompt, response])
        if streaming:
            async with ai.stream(model, [prompt]) as stream:
                async for _ in stream:
                    pass
            assert stream.message.text == "hello"
        else:
            assert (await ai.experimental_generate(model, [prompt])).text == "hello"


async def tools():
    @ai.tool
    async def double(value: int) -> int:
        """Double a number."""
        current = ai.current_tool_call()
        assert current is not None
        return 2 * value

    prompt = ai.user_message("Double 6")
    model = ai.testing.FakeModel(
        [
            prompt,
            ai.assistant_message(ai.testing.tool_call(double, value=6)),
            ai.assistant_message("12"),
        ]
    )
    async with ai.Agent(tools=[double]).run(model, [prompt]) as stream:
        async for _ in stream:
            pass
    assert not model.unused


async def structured():
    class Answer(pydantic.BaseModel):
        value: int

    prompt = ai.user_message("Return 42 as JSON")
    model = ai.testing.FakeModel([prompt, ai.assistant_message('{"value":42}')])
    async with ai.stream(model, [prompt], output_type=Answer) as stream:
        async for _ in stream:
            pass
    assert stream.output.value == 42


async def multimodal():
    prompt = ai.user_message(
        "Describe this", FilePart(data=b"example", media_type="image/png")
    )
    model = ai.testing.FakeModel([prompt, ai.assistant_message("image received")])
    await ai.experimental_generate(model, [prompt])


async def operations():
    model = ai.Model(id="example-multimodal", provider=ExampleProvider())
    assert (await ai.ops.embed(model, ["alpha", "beta"])).value == [
        [0.25, 0.75],
        [0.25, 0.75],
    ]
    await ai.ops.generate_image(model, "an example image")
    await ai.ops.generate_video(model, "an example video")
    await ai.ops.generate_audio(model, "say hello")
    await ai.ops.transcribe(model, b"example-audio")
    await ai.ops.rerank(model, ["low", "high"], "high")
    answer = await ai.ops.experimental.evaluate(
        model,
        "4 is even",
        {"correct": ai.ops.experimental.NoulQuestion(instructions="Is this correct?")},
    )
    assert answer.value["correct"].noul == 0.95


async def typed_evaluation():
    class Questions(pydantic.BaseModel):
        correct: ai.ops.experimental.NoulQuestion

    class Answers(pydantic.BaseModel):
        correct: ai.ops.experimental.NoulAnswer

    answer = await ai.ops.experimental.evaluate(
        ai.Model(id="example-evaluation", provider=ExampleProvider()),
        "4 is even",
        Questions(
            correct=ai.ops.experimental.NoulQuestion(instructions="Is this correct?")
        ),
        output_type=Answers,
    )
    assert isinstance(answer.value, Answers)
    assert answer.value.correct.noul == 0.95


async def errors():
    model = ai.Model(id="example-embedding-error", provider=ExampleProvider())
    try:
        await ai.ops.embed(model, ["expected error"])
    except ValueError as exc:
        assert str(exc) == "Expected embedding example failure"
    else:
        raise AssertionError("Expected provider exception")


async def hooks():
    data = telemetry.HookSpanData(
        label="example approval", hook_type="tool", metadata={"tool": "read"}
    )
    async with telemetry.span(data) as span:
        span.data.status = "resolved"
        span.data.resolution = {"granted": True}


async def durable_replay():
    sink = telemetry.DictSink()
    async with telemetry.use_sink(sink), telemetry.span("serialized workflow"):
        await text()
        await operations()
        await typed_evaluation()
    payload = [span.model_dump(mode="json") for span in sink.finished_spans]
    await telemetry.push_all(payload)


async def runtime_privacy():
    token = otel_context.attach(
        otel_context.set_value(ENABLE_CONTENT_TRACING_KEY, False)
    )
    try:
        await tools()
        await ai.ops.embed(
            ai.Model(id="private-embedding", provider=ExampleProvider()),
            ["private embedding input"],
        )
    finally:
        otel_context.detach(token)


async def live():
    model = ai.Model(
        id=os.environ.get("RESPAN_EXAMPLE_MODEL", "gpt-4o-mini"),
        provider=ai.get_provider(
            "openai",
            base_url="https://api.respan.ai/api",
            api_key=os.environ["RESPAN_API_KEY"],
            protocol=OpenAIChatCompletionsProtocol(),
        ),
    )
    try:
        async with ai.stream(
            model, [ai.user_message("Reply only: live verification OK")]
        ) as stream:
            async for _ in stream:
                pass
        assert stream.message.text
    finally:
        await model.provider.aclose()


async def main(args):
    if args.no_export and (args.live or args.env_file):
        raise ValueError("--no-export cannot be combined with --live or --env-file")
    for file in args.env_file:
        load_dotenv(file, override=False)
    if not args.no_export and not os.environ.get("RESPAN_API_KEY"):
        raise RuntimeError("RESPAN_API_KEY is required")
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    memory = InMemorySpanExporter()
    sent_payloads = []
    if not args.no_export:
        exporter = RespanSpanExporter(
            endpoint=os.environ.get("RESPAN_BASE_URL", "https://api.respan.ai/api"),
            api_key=os.environ["RESPAN_API_KEY"],
        )
        # Preserve the actual sent OTLP body for comparison with scoped MCP records.
        post = exporter._session.post

        def record_post(*positional, **keywords):
            sent_payloads.append(json.loads(keywords["data"]))
            return post(*positional, **keywords)

        exporter._session.post = record_post
        provider.add_span_processor(SimpleSpanProcessor(exporter))
    provider.add_span_processor(SimpleSpanProcessor(memory))
    instrumentor = VercelInstrumentor()
    instrumentor.activate()
    retained_embed = ai.ops.embed

    async def private_calls():
        await tools()
        await typed_evaluation()
        await retained_embed(
            ai.Model(id="private-embedding", provider=ExampleProvider()),
            ["private embedding input"],
        )

    tracer = provider.get_tracer("respan.examples.vercel")
    manifest = {"run_id": args.run_id, "sdk_version": version("ai"), "scenarios": []}
    scenarios = [
        ("text", text),
        ("tools", tools),
        ("structured", structured),
        ("multimodal", multimodal),
        ("operations", operations),
        ("typed_evaluation", typed_evaluation),
        ("errors", errors),
        ("hooks", hooks),
        ("durable_replay", durable_replay),
        ("runtime_privacy", runtime_privacy),
    ]
    if args.live:
        scenarios.append(("live_gateway", live))
    try:
        for name, function in scenarios + [("privacy", private_calls)]:
            if name == "privacy":
                instrumentor.deactivate()
                instrumentor = VercelInstrumentor(capture_content=False)
                instrumentor.activate()
            before = len(memory.get_finished_spans())
            attrs = {
                RESPAN_LOG_TYPE: "workflow",
                SpanAttributes.TRACELOOP_ENTITY_NAME: f"vercel-python-{name}",
                RESPAN_METADATA: json.dumps({"run_id": args.run_id, "scenario": name}),
            }
            with tracer.start_as_current_span(
                f"vercel-python-{name}", attributes=attrs
            ) as parent:
                trace_id = f"{parent.get_span_context().trace_id:032x}"
                try:
                    await asyncio.wait_for(function(), timeout=90)
                    status = "passed"
                except Exception as exc:  # noqa: BLE001 - record each failed scenario
                    status = "failed"
                    # Keep provider failures distinguishable from translator checks.
                    error = f"{type(exc).__name__}: {str(exc)[:300]}"
            spans = memory.get_finished_spans()[before:]
            failures = [
                span
                for span in spans
                if span.status.status_code == trace.StatusCode.ERROR
            ]
            if failures and name != "errors":
                status = "failed"
                error = "; ".join(
                    span.status.description or span.name for span in failures
                )
            record = {
                "name": name,
                "trace_id": trace_id,
                "status": status,
                "span_count": len(spans),
                "span_ids": [f"{s.context.span_id:016x}" for s in spans],
            }
            if status == "failed":
                record["error"] = error
            manifest["scenarios"].append(record)
            print(json.dumps(record), flush=True)
    finally:
        instrumentor.deactivate()
        provider.force_flush()
        provider.shutdown()
        Path(args.output).write_text(json.dumps(manifest, indent=2) + "\n")
        Path(args.output).with_suffix(".spans.json").write_text(
            json.dumps(
                [json.loads(span.to_json()) for span in memory.get_finished_spans()],
                indent=2,
            )
            + "\n"
        )
        Path(args.output).with_suffix(".otlp.json").write_text(
            json.dumps(sent_payloads, indent=2) + "\n"
        )
    if any(s["status"] != "passed" for s in manifest["scenarios"]):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", action="append", default=[])
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Run fixtures locally without keys or network",
    )
    parser.add_argument("--run-id", default=f"vercel-python-{int(time.time())}")
    parser.add_argument("--output", default="verification.json")
    asyncio.run(main(parser.parse_args()))
