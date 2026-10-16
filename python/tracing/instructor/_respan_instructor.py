"""Fixture-default native clients and an explicit Respan export pipeline."""

import importlib
import inspect
import os
import uuid
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

import instructor
from _fixtures import client_context
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic import BaseModel, Field
from respan_instrumentation_instructor import InstructorInstrumentor
from respan_tracing import RespanTelemetry
from respan_tracing import workflow as native_workflow
from respan_tracing.exporters import propagate_attributes

REPO_ROOT = Path(__file__).resolve().parents[3]


class User(BaseModel):
    name: str
    age: int = Field(ge=0)


class _Tracing:
    def __init__(self, app_name):
        export = os.getenv("RESPAN_EXAMPLE_EXPORT") == "1"
        if export or os.getenv("INSTRUCTOR_EXAMPLE_MODE") == "live":
            load_dotenv(
                Path(os.getenv("RESPAN_EXAMPLE_ENV_FILE", REPO_ROOT / ".env")),
                override=False,
            )
        existing = os.environ.pop("RESPAN_API_KEY", None) if not export else None
        try:
            self.telemetry = RespanTelemetry(
                app_name=app_name,
                api_key=os.environ["RESPAN_API_KEY"] if export else None,
                base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
                is_auto_instrument=False,
                is_batching_enabled=False,
                log_level="WARNING",
            )
        finally:
            if existing is not None:
                os.environ["RESPAN_API_KEY"] = existing
        self.memory = InMemorySpanExporter()
        self.telemetry.add_processor(self.memory, is_batching_enabled=False)
        self.instrumentor = InstructorInstrumentor(
            tracer_provider=self.telemetry.tracer.tracer_provider
        )
        self.instrumentor.activate()
        self.contexts = []
        self.native_clients = []
        self.attribute_context = attributes(app_name)
        self.attribute_context.__enter__()

    def shutdown(self):
        self.instrumentor.deactivate()
        for manager in reversed(self.contexts):
            manager.__exit__(None, None, None)
        for client in self.native_clients:
            client.close()
        self.attribute_context.__exit__(None, None, None)
        self.telemetry.flush()
        self.telemetry.tracer.tracer_provider.shutdown()


def create_respan_instructor_client(
    *, app_name, async_client=False, responses=False, **options
):
    tracing = _Tracing(app_name)
    if os.getenv("INSTRUCTOR_EXAMPLE_MODE", "fixture") == "live":
        key = os.getenv("INSTRUCTOR_PROVIDER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not key:
            tracing.shutdown()
            raise ValueError(
                "Live mode requires INSTRUCTOR_PROVIDER_API_KEY or OPENAI_API_KEY"
            )
        cls = AsyncOpenAI if async_client else OpenAI
        native = cls(
            api_key=key,
            base_url=os.getenv(
                "INSTRUCTOR_PROVIDER_BASE_URL", "https://api.openai.com/v1"
            ),
        )
        client = instructor.from_openai(
            native,
            mode=instructor.Mode.RESPONSES_TOOLS
            if responses
            else instructor.Mode.TOOLS,
        )
        if not async_client:
            tracing.native_clients.append(native)
    else:
        manager = client_context(
            async_client=async_client, responses=responses, **options
        )
        client, _ = manager.__enter__()
        tracing.contexts.append(manager)
    if hasattr(client, "kwargs"):
        client.kwargs["model"] = os.getenv(
            "INSTRUCTOR_MODEL",
            "fixture-model"
            if os.getenv("INSTRUCTOR_EXAMPLE_MODE", "fixture") != "live"
            else "gpt-4o-mini",
        )
    return tracing, client


def retry_exception_type():
    for path in (
        "instructor.v2.core.errors",
        "instructor.core.exceptions",
        "instructor.exceptions",
    ):
        try:
            return importlib.import_module(path).InstructorRetryException
        except (ImportError, AttributeError):
            continue
    raise ImportError("Released Instructor retry exception unavailable")


@contextmanager
def attributes(script):
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID", "instructor-" + uuid.uuid4().hex[:12])
    with propagate_attributes(
        metadata={
            "run_id": marker,
            "example_set": "instructor",
            "example_script": script,
        },
        thread_identifier=script,
    ):
        yield marker


def workflow(*, name):
    """Keep SDK clients out of decorated inputs while retaining native workflows."""

    def decorate(function):
        if inspect.iscoroutinefunction(function):

            @wraps(function)
            async def wrapped(*args, **kwargs):
                @native_workflow(name=name)
                async def invoke():
                    return await function(*args, **kwargs)

                return await invoke()
        else:

            @wraps(function)
            def wrapped(*args, **kwargs):
                @native_workflow(name=name)
                def invoke():
                    return function(*args, **kwargs)

                return invoke()

        return wrapped

    return decorate
