"""Exercise current Langfuse SDK spans through the linked Respan instrumentor."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env", override=False)

os.environ.setdefault("LANGFUSE_PUBLIC_KEY", "pk-lf-respan-example")
os.environ.setdefault("LANGFUSE_SECRET_KEY", "sk-lf-respan-example")
os.environ.setdefault("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

from langfuse import get_client, observe, propagate_attributes
from respan import Respan
from respan_instrumentation_langfuse import LangfuseInstrumentor

RUN_ID = (
    os.getenv("RESPAN_EXAMPLE_RUN_ID", "").strip() or f"langfuse-{uuid4().hex[:12]}"
)
MODEL = os.getenv("RESPAN_LANGFUSE_MODEL", "gpt-4o-mini")
EXPECTED_SPANS = 14


def _mark_trace(workflow_name: str, input_value: object) -> None:
    get_client().update_current_span(
        input=input_value,
        metadata={
            "example": "langfuse",
            "example_run_id": RUN_ID,
            "run_id": RUN_ID,
            "workflow_name": workflow_name,
        },
    )


@observe(as_type="generation", name="answer-question")
def answer_question(question: str) -> str:
    answer = f"A concise answer about: {question}"
    get_client().update_current_generation(
        input=[{"role": "user", "content": question}],
        output=[{"role": "assistant", "content": answer}],
        model=MODEL,
        usage_details={
            "prompt_tokens": 9,
            "completion_tokens": 7,
            "total_tokens": 16,
        },
        metadata={"example_run_id": RUN_ID},
    )
    return answer


@observe(as_type="tool", name="search-source")
def search_source(source: str, query: str) -> dict[str, str]:
    result = {"source": source, "result": f"{source} evidence for {query}"}
    get_client().update_current_span(
        output=result,
        metadata={"example_run_id": RUN_ID},
    )
    return result


@observe(name="langfuse_simple.workflow")
def simple_workflow() -> str:
    _mark_trace("langfuse_simple.workflow", {"question": "What is tracing?"})
    return answer_question("What is tracing?")


@observe(name="langfuse_research.workflow")
def research_workflow() -> str:
    query = "OpenTelemetry"
    _mark_trace("langfuse_research.workflow", {"query": query})
    evidence = [
        search_source("docs", query),
        search_source("examples", query),
    ]
    return answer_question(
        f"Summarize {query} using {', '.join(item['source'] for item in evidence)}"
    )


@observe(as_type="agent", name="embedding-agent")
def embedding_agent() -> list[list[float]]:
    vectors = [[0.25, 0.5, 0.75]]
    with get_client().start_as_current_observation(
        name="embed-source",
        as_type="embedding",
        model="example-embedding-model",
        input=["OpenTelemetry"],
        output=vectors,
        usage_details={"input": 3, "total": 3},
    ):
        pass
    return vectors


@observe(as_type="guardrail", name="validate-query")
def validate_query(query: str) -> dict[str, bool]:
    return {"allowed": bool(query.strip())}


@observe(as_type="tool", name="controlled-failure")
def controlled_failure() -> None:
    raise ValueError("Deterministic Langfuse example failure")


@observe(name="langfuse_features.workflow")
def features_workflow() -> dict[str, object]:
    _mark_trace("langfuse_features.workflow", {"query": "OpenTelemetry"})
    result = {
        "guardrail": validate_query("OpenTelemetry"),
        "embedding": embedding_agent(),
    }
    try:
        controlled_failure()
    except ValueError:
        result["controlled_error"] = True
    return result


@observe(name="langfuse_async.workflow")
async def async_workflow() -> dict[str, object]:
    _mark_trace("langfuse_async.workflow", {"query": "weather in Paris"})
    call = {
        "id": "call-weather-current",
        "type": "function",
        "function": {"name": "weather", "arguments": '{"city":"Paris"}'},
    }
    definition = {
        "type": "function",
        "function": {"name": "weather", "parameters": {"type": "object"}},
    }
    with get_client().start_as_current_observation(
        name="single-message-tool-call",
        as_type="generation",
        model=MODEL,
        input={"role": "user", "content": "Check the weather in Paris"},
        output={"role": "assistant", "content": None, "tool_calls": [call]},
        model_parameters={"tools": [definition]},
        usage_details={"input": 7, "output": 3},
    ):
        await asyncio.sleep(0)
    # Missing captured content must stay absent instead of becoming a null prompt.
    with get_client().start_as_current_observation(
        name="usage-only-generation",
        as_type="generation",
        model=MODEL,
        usage_details={"input": 2, "output": 1},
    ):
        await asyncio.sleep(0)
    return {"tool_call": call, "content_free_generation": True}


def main() -> None:
    print(f"run_id={RUN_ID}", flush=True)
    api_key = os.environ["RESPAN_API_KEY"]
    respan = Respan(
        api_key=api_key,
        base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
        app_name="langfuse-current-sdk",
        instrumentations=[],
        is_batching_enabled=False,
    )
    instrumentor = LangfuseInstrumentor()
    instrumentor.instrument()
    client = get_client()

    try:
        for workflow in (simple_workflow, research_workflow, features_workflow):
            with propagate_attributes(
                user_id="langfuse-example-user",
                session_id=f"{RUN_ID}:session",
                trace_name=f"langfuse_{workflow.__name__.removesuffix('_workflow')}.workflow",
                metadata={"run_id": RUN_ID, "example_run_id": RUN_ID},
            ):
                print(workflow())
        with propagate_attributes(
            user_id="langfuse-example-user",
            session_id=f"{RUN_ID}:session",
            trace_name="langfuse_async.workflow",
            metadata={"run_id": RUN_ID, "example_run_id": RUN_ID},
        ):
            print(asyncio.run(async_workflow()))
        client.flush()
        respan.flush()
        if instrumentor.exported_span_count != EXPECTED_SPANS:
            raise RuntimeError(
                "Langfuse exported "
                f"{instrumentor.exported_span_count} spans; expected {EXPECTED_SPANS}"
            )
        print(f"Langfuse exported {EXPECTED_SPANS} canonical spans.")
    finally:
        client.shutdown()
        instrumentor.uninstrument()
        respan.shutdown()


if __name__ == "__main__":
    main()
