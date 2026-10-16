"""Controlled real SDK fixtures, local spans by default, explicit export opt-in."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from contextlib import contextmanager
from pathlib import Path

import httpx
from dotenv import load_dotenv
from livekit.agents import function_tool, llm, telemetry
from livekit.agents.types import APIConnectOptions
from livekit.plugins import openai as plugin
from openai import AsyncOpenAI
from opentelemetry import trace
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan_instrumentation_livekit import LiveKitInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_METADATA

EXAMPLE_DIR = Path(__file__).resolve().parent
EXPORT = os.getenv("RESPAN_EXPORT", "0") == "1"
if EXPORT or os.getenv("RESPAN_LIVEKIT_LIVE", "0") == "1":
    load_dotenv(
        Path(os.getenv("RESPAN_ENV_FILE", str(EXAMPLE_DIR.parents[2] / ".env"))),
        override=False,
    )
RUN_ID = os.getenv("RESPAN_EXAMPLE_RUN_ID") or "livekit-" + uuid.uuid4().hex[:12]


def example_run_id():
    if (
        RUN_ID != RUN_ID.strip()
        or any(c in RUN_ID for c in "\r\n")
        or len(RUN_ID.encode()) > 160
    ):
        raise ValueError(
            "Exact marker must be at most160 bytes without whitespace/newlines"
        )
    return RUN_ID


class Marker(SpanProcessor):
    def __init__(self, scenario):
        self.metadata = {
            "run_id": example_run_id(),
            "example_run_id": example_run_id(),
            "framework": "livekit",
            "scenario": scenario,
            "example": scenario,
            "example_set": "python/tracing/livekit",
        }

    def on_start(self, span, parent_context=None):
        span.set_attribute(RESPAN_METADATA, json.dumps(self.metadata))
        for k, v in self.metadata.items():
            span.set_attribute(RESPAN_METADATA + "." + k, v)

    def on_end(self, span):
        pass

    def shutdown(self):
        pass

    def force_flush(self, timeout_millis=30000):
        return True


class Tracing:
    def __init__(self, scenario, *, capture_content=True):
        if EXPORT:
            from respan_tracing import RespanTelemetry

            RespanTelemetry(
                app_name="livekit-" + scenario,
                api_key=os.environ["RESPAN_API_KEY"],
                base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
                is_auto_instrument=False,
                is_batching_enabled=False,
            )
            self.provider = trace.get_tracer_provider()
        else:
            self.provider = TracerProvider()
            trace.set_tracer_provider(self.provider)
        self.exporter = InMemorySpanExporter()
        self.provider.add_span_processor(Marker(scenario))
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self.owner = LiveKitInstrumentor(capture_content=capture_content)
        self.owner.activate()

    def finish(self):
        self.provider.force_flush()
        self.owner.deactivate()
        spans = self.exporter.get_finished_spans()
        print("LOCAL_TRACE_COUNT=" + str(len(spans)))
        directory = os.getenv("LIVEKIT_CAPTURE_DIR")
        if directory:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            path.joinpath(f"{RUN_ID}-{os.getpid()}.json").write_text(
                json.dumps(
                    [
                        {
                            "name": s.name,
                            "span_id": f"{s.context.span_id:016x}",
                            "trace_id": f"{s.context.trace_id:032x}",
                            "parent_id": f"{s.parent.span_id:016x}"
                            if s.parent
                            else None,
                            "status": s.status.status_code.name,
                            "attributes": dict(s.attributes),
                            "events": [
                                {"name": e.name, "attributes": dict(e.attributes)}
                                for e in s.events
                            ],
                        }
                        for s in spans
                    ],
                    indent=2,
                )
            )
        self.provider.shutdown()


@contextmanager
def native_job():
    with telemetry.tracer.start_as_current_span("job_entrypoint") as span:
        yield span


def chat_context(history=False):
    ctx = llm.ChatContext.empty()
    ctx.add_message(role="system", content="Controlled native SDK instructions")
    if history:
        ctx.insert(
            llm.FunctionCall(
                call_id="history-only", name="previous", arguments='{"x":1}'
            )
        )
        ctx.insert(
            llm.FunctionCallOutput(
                call_id="history-only",
                name="previous",
                output=json.dumps({"vector": list(range(5000))}),
                is_error=False,
            )
        )
    ctx.add_message(role="user", content="controlled input")
    return ctx


SCHEMA = {
    "name": "vector_tool",
    "description": "Controlled native vector tool",
    "parameters": {
        "type": "object",
        "properties": {
            "dense": {"type": "array", "items": {"type": "integer"}},
            "sparse": {"type": "object"},
            "api_key": {
                "type": "string",
                "default": "PRIVATE_CREDENTIAL",
                "examples": ["PRIVATE_EXAMPLE"],
            },
            **{f"field{i}": {"type": "integer"} for i in range(120)},
        },
    },
}


@function_tool(raw_schema=SCHEMA)
async def vector_tool(raw_arguments: dict[str, object]):
    return {"dense": raw_arguments["dense"], "sparse": raw_arguments["sparse"]}


@function_tool
async def lookup_room_status(room: str) -> str:
    return f"Room {room} has two participants"


class FixtureLLM(llm.LLM):
    def __init__(
        self, *, scenario="text", usage=True, pause=None, finish=None, boundary=None
    ):
        super().__init__()
        self.scenario = scenario
        self.usage = usage
        self.pause = pause
        self.finish = finish
        self.boundary = boundary

    @property
    def model(self):
        return "fixture-model"

    @property
    def provider(self):
        return "openai"

    def chat(self, *, chat_ctx, tools=None, conn_options=None, **kwargs):
        return FixtureStream(
            self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options or APIConnectOptions(max_retry=0),
        )

    async def aclose(self):
        pass


class FixtureStream(llm.LLMStream):
    async def _run(self):
        if self._llm.pause:
            await self._llm.pause.wait()
        if self._llm.boundary:
            self._llm.boundary()
        if self._llm.scenario == "tools":
            calls = [
                llm.FunctionToolCall(
                    name="vector_tool",
                    arguments=json.dumps(
                        {
                            "dense": list(range(5000)),
                            "sparse": {j * 2: j / 256 for j in range(256)},
                            "api_key": "PRIVATE_CREDENTIAL",
                            "content": 'Bearer synthetic-token"quoted" value',
                        }
                    ),
                    call_id=f"actual-vector-{i}",
                )
                for i in range(2)
            ]
            self._event_ch.send_nowait(
                llm.ChatChunk(
                    id="actual",
                    delta=llm.ChoiceDelta(role="assistant", tool_calls=calls),
                )
            )
        else:
            for word in ["native ", "LiveKit ", "output"]:
                self._event_ch.send_nowait(
                    llm.ChatChunk(
                        id="actual",
                        delta=llm.ChoiceDelta(role="assistant", content=word),
                    )
                )
                await asyncio.sleep(0)
        if self._llm.finish:
            await self._llm.finish.wait()
        if self._llm.usage:
            values = {
                "prompt_tokens": 11,
                "completion_tokens": 7,
                "total_tokens": 18,
                "prompt_cached_tokens": 3,
            }
            if "reasoning_tokens" in llm.CompletionUsage.model_fields:
                values["reasoning_tokens"] = 2
            if "cache_creation_tokens" in llm.CompletionUsage.model_fields:
                values["cache_creation_tokens"] = 4
            self._event_ch.send_nowait(
                llm.ChatChunk(id="actual", usage=llm.CompletionUsage(**values))
            )


def provider_model(*, usage=True, error=False, live=False):
    if live:
        client = AsyncOpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.getenv("OPENAI_BASE_URL"),
            max_retries=0,
        )
        return plugin.LLM(
            model=os.getenv("RESPAN_LIVEKIT_MODEL", "gpt-4.1-mini"), client=client
        ), client

    def boundary(request):
        if error:
            return httpx.Response(
                429,
                json={
                    "error": {
                        "message": "controlled provider failure",
                        "type": "rate_limit_error",
                    }
                },
            )
        frames = [
            {
                "id": "actual-openai",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": "fixture-model",
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": "actual provider fixture",
                        },
                        "finish_reason": None,
                    }
                ],
            },
            {
                "id": "actual-openai",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": "fixture-model",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            },
        ]
        if usage is not False:
            counts = {
                "prompt_tokens": 11,
                "completion_tokens": 7,
                "total_tokens": 18,
                "prompt_tokens_details": {"cached_tokens": 3},
                "completion_tokens_details": {"reasoning_tokens": 2},
            }
            if isinstance(usage, dict):
                counts = usage
            frames.append(
                {
                    "id": "actual-openai",
                    "object": "chat.completion.chunk",
                    "created": 1,
                    "model": "fixture-model",
                    "choices": [],
                    "usage": counts,
                }
            )
        return httpx.Response(
            200,
            content="".join("data: " + json.dumps(f) + "\n\n" for f in frames)
            + "data: [DONE]\n\n",
            headers={"content-type": "text/event-stream"},
        )

    client = AsyncOpenAI(
        api_key="synthetic",
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(boundary)),
    )
    return plugin.LLM(model="fixture-model", client=client), client
