"""Shared setup helpers for DSPy + Respan examples."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import dspy
from dotenv import load_dotenv
from opentelemetry.semconv_ai import SpanAttributes
from respan import Respan
from respan_instrumentation_dspy import DSPyInstrumentor

DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
DEFAULT_DSPY_MODEL = "openai/gpt-4o-mini"


@dataclass(frozen=True)
class GatewaySettings:
    api_key: str
    base_url: str
    model: str


@dataclass(frozen=True)
class ExampleContext:
    respan: Respan
    settings: GatewaySettings
    example_name: str
    run_id: str


@dataclass(frozen=True)
class ExampleSpan:
    span: Any | None

    def set_input(self, value: object) -> None:
        _set_json_attribute(
            span=self.span,
            attribute=SpanAttributes.TRACELOOP_ENTITY_INPUT,
            value=value,
        )

    def set_output(self, value: object) -> None:
        _set_json_attribute(
            span=self.span,
            attribute=SpanAttributes.TRACELOOP_ENTITY_OUTPUT,
            value=value,
        )


def load_gateway_settings() -> GatewaySettings:
    """Load env files and return gateway settings for DSPy."""
    _load_env_files()
    api_key = os.environ["RESPAN_API_KEY"]
    base_url = os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL)
    model = (
        os.getenv("RESPAN_DSPY_MODEL")
        or os.getenv("RESPAN_MODEL")
        or DEFAULT_DSPY_MODEL
    )

    return GatewaySettings(
        api_key=api_key,
        base_url=base_url,
        model=_normalize_dspy_model(model),
    )


def create_respan(
    *,
    app_name: str,
    example_name: str,
    include_content: bool = True,
    temperature: float = 0.2,
) -> ExampleContext:
    """Start Respan tracing and configure DSPy gateway routing."""
    settings = load_gateway_settings()
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID") or uuid4().hex[:8]
    metadata = {
        "example_set": "dspy",
        "example_name": example_name,
        "example_run_id": run_id,
        "run_id": run_id,
    }
    respan = Respan(
        api_key=settings.api_key,
        base_url=settings.base_url,
        app_name=app_name,
        metadata=metadata,
        is_batching_enabled=False,
        instrumentations=[
            DSPyInstrumentor(include_content=include_content),
        ],
    )
    if os.getenv("RESPAN_DSPY_MODEL_MODE", "fixture") == "live":
        model = dspy.LM(
            settings.model,
            api_key=settings.api_key,
            api_base=settings.base_url,
            cache=False,
            temperature=temperature,
        )
    else:
        model = FixtureLM(fixture_replies(example_name), temperature=temperature)
    dspy.configure(lm=model)
    return ExampleContext(
        respan=respan,
        settings=settings,
        example_name=example_name,
        run_id=run_id,
    )


@contextmanager
def managed_example(
    *,
    app_name: str,
    example_name: str,
    include_content: bool = True,
    temperature: float = 0.2,
):
    """Create one example context and always shut down its exporter."""
    context = create_respan(
        app_name=app_name,
        example_name=example_name,
        include_content=include_content,
        temperature=temperature,
    )
    try:
        yield context
    finally:
        context.respan.shutdown()


@contextmanager
def traced_example(
    context: ExampleContext,
    *,
    root_span_name: str | None = None,
    input_data: object | None = None,
):
    """Group one script run under a recognizable root workflow span."""
    span_name = root_span_name or f"dspy_example_{context.example_name}"
    with context.respan.propagate_attributes(
        trace_group_identifier=f"{context.example_name}-{context.run_id}",
        custom_identifier=context.run_id,
        thread_identifier=f"dspy_example_{context.example_name}",
        metadata={
            "example_set": "dspy",
            "example_name": context.example_name,
            "example_run_id": context.run_id,
            "run_id": context.run_id,
        },
    ):
        client = context.respan.telemetry.get_client()
        with client.start_span(span_name, kind="workflow") as span:
            example_span = ExampleSpan(span=span)
            if input_data is not None:
                example_span.set_input(input_data)
            yield example_span


def print_result(label: str, value: object) -> None:
    print(f"{label}: {value}")


def _normalize_dspy_model(model: str) -> str:
    if "/" in model:
        return model
    return f"openai/{model}"


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


def _set_json_attribute(*, span: Any | None, attribute: str, value: object) -> None:
    if span is None:
        return
    try:
        payload = json.dumps(value, default=str)
    except (TypeError, ValueError):
        payload = str(value)
    if len(payload) < 1_000_000:
        span.set_attribute(attribute, payload)


def formatted(**fields) -> str:
    return (
        "\n".join(
            f"[[ ## {key} ## ]]\n{value if isinstance(value, str) else json.dumps(value)}"
            for key, value in fields.items()
        )
        + "\n[[ ## completed ## ]]"
    )


def fixture_replies(name: str) -> list[str]:
    return {
        "01_predict_signature": [
            formatted(
                answer="DSPy builds language model programs from signatures and modules."
            )
        ],
        "02_chain_of_thought": [
            formatted(
                reasoning="The controlled trace shows added retrieval and model calls.",
                summary="Review retrieval timing and the prompt change.",
            )
        ],
        "03_module_workflow": [
            formatted(
                context="A trace connects module, adapter, model and tool calls."
            ),
            formatted(
                reasoning="Their shared parent shows the workflow.",
                answer="One tree makes the program's call relationships visible.",
            ),
        ],
        "05_react_agent": [
            formatted(
                next_thought="Look up Tokyo.",
                next_tool_name="lookup_city_fact",
                next_tool_args={"city": "Tokyo"},
            ),
            formatted(
                next_thought="The fact is available.",
                next_tool_name="finish",
                next_tool_args={},
            ),
            formatted(
                reasoning="The tool supplied the city fact.",
                answer="Tokyo has one of the world's busiest rail networks.",
            ),
        ],
        "06_evaluate_program": [formatted(answer="Paris")],
        "07_async_calls": [formatted(answer="async fixture")],
    }.get(name, [])


class FixtureLM(dspy.BaseLM):
    """Controlled OpenAI-shaped provider responses using the released BaseLM API.

    The legacy subclass interface supports both DSPy3.0 and3.4; the separate
    lm15 example exercises3.4's preferred native engine API.
    """

    def __init__(self, replies, **kwargs):
        super().__init__("openai/fixture-dspy", cache=False, **kwargs)
        self.replies = iter(replies)

    def forward(self, prompt=None, messages=None, **kwargs):
        from litellm import ModelResponse

        value = next(self.replies)
        if isinstance(value, BaseException):
            raise value
        return ModelResponse(
            model="fixture-dspy",
            id="controlled-dspy-response",
            choices=[
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": value},
                }
            ],
            usage={
                "prompt_tokens": 11,
                "completion_tokens": 7,
                "total_tokens": 18,
                "prompt_tokens_details": {"cached_tokens": 3},
                "completion_tokens_details": {"reasoning_tokens": 2},
            },
        )

    async def aforward(self, prompt=None, messages=None, **kwargs):
        import asyncio

        await asyncio.sleep(0)
        return self.forward(prompt, messages, **kwargs)


def native_model(responses):
    """DSPy3.4 custom engine fixture with sync and async stream methods."""
    from collections import deque

    from dspy.lm15 import response_to_events

    queue = deque(responses)

    class Engine:
        def complete(self, request):
            return queue.popleft()

        def stream(self, request):
            yield from response_to_events(queue.popleft())

        def close(self):
            pass

    class AsyncEngine:
        async def complete(self, request):
            return queue.popleft()

        async def stream(self, request):
            for event in response_to_events(queue.popleft()):
                yield event

        async def aclose(self):
            pass

    return dspy.LM(
        "openai/fixture-dspy",
        engine=Engine(),
        async_engine=AsyncEngine(),
        cache=False,
        num_retries=0,
    )
