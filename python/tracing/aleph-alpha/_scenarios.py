"""Actual released SDK APIs on controlled HTTP/SSE; paid calls are explicit."""

from __future__ import annotations

import asyncio
import gc
import os
import threading
from contextlib import contextmanager
from http.server import ThreadingHTTPServer

from _fixture import Handler
from aleph_alpha_client import (
    AsyncClient,
    BatchSemanticEmbeddingRequest,
    ChatRequest,
    Client,
    CompletionRequest,
    EmbeddingRequest,
    EmbeddingV2Request,
    EvaluationRequest,
    ExplanationRequest,
    Message,
    Prompt,
    SemanticEmbeddingRequest,
    SemanticRepresentation,
)
from aleph_alpha_client.chat import Role, StreamOptions
from aleph_alpha_client.embedding import InstructableEmbeddingRequest
from opentelemetry import context, trace

MODEL = os.getenv("ALEPH_ALPHA_MODEL", "controlled-aleph-model")


@contextmanager
def host_context(case):
    if os.getenv("ALEPH_ALPHA_EXAMPLE_REAL") == "1":
        if case not in {
            "chat",
            "completion",
            "embeddings",
            "async-streaming",
            "evaluate-explain",
            "async-apis",
        }:
            raise RuntimeError(
                "Privacy and lifecycle fault fixtures require controlled mode"
            )
        token = os.getenv("ALEPH_ALPHA_API_KEY")
        host = os.getenv("ALEPH_ALPHA_HOST")
        model = os.getenv("ALEPH_ALPHA_MODEL")
        if not token or not host or not model:
            raise RuntimeError(
                "Real mode requires ALEPH_ALPHA_API_KEY, ALEPH_ALPHA_HOST and ALEPH_ALPHA_MODEL"
            )
        yield host, token
        return
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/", "controlled-fixture-token"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def request(method, text="native controlled input"):
    prompt = Prompt.from_text(text)
    if method.startswith("chat"):
        return ChatRequest(
            model=MODEL,
            messages=[Message(Role.User, text)],
            stream_options=StreamOptions(include_usage=True),
        )
    if method.startswith("complete"):
        return CompletionRequest(
            prompt, maximum_tokens=16, temperature=0.0, stop_sequences=[]
        )
    if method == "embed":
        return EmbeddingRequest(prompt, layers=[-1], pooling=["mean"])
    if method == "embeddings":
        return EmbeddingV2Request([text, "second"])
    if method == "semantic_embed":
        return SemanticEmbeddingRequest(prompt, SemanticRepresentation.Query)
    if method == "batch_semantic_embed":
        return BatchSemanticEmbeddingRequest(
            [prompt, prompt], SemanticRepresentation.Document
        )
    if method == "instructable_embed":
        return InstructableEmbeddingRequest(prompt, "native instruction")
    if method == "evaluate":
        return EvaluationRequest(prompt, completion_expected="native completion")
    return ExplanationRequest(prompt, target="native target")


def sync_case(case, provider):
    with host_context(case) as (host, token):
        client = Client(token=token, host=host, total_retries=0)
        try:
            if case == "chat":
                schema = {
                    "type": "object",
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "default": "PRIVATE-SCHEMA",
                            "example": "PRIVATE-SCHEMA",
                        },
                        "count": {"type": "integer", "default": 0},
                    },
                    "required": ["api_key"],
                }
                messages = (
                    [Message(Role.User, f"history {i}") for i in range(75)]
                    if os.getenv("ALEPH_ALPHA_EXAMPLE_REAL") != "1"
                    else [Message(Role.User, "Explain tracing")]
                )
                req = ChatRequest(
                    model=MODEL,
                    messages=messages,
                    tools=[
                        {
                            "type": "function",
                            "function": {"name": "lookup_policy", "parameters": schema},
                        }
                    ],
                    parallel_tool_calls=False,
                )
                result = client.chat(req, MODEL)
                return {
                    "native_type": type(result).__name__,
                    "tool_ids": [tool.id for tool in result.message.tool_calls or []],
                }
            if case == "completion":
                result = client.complete(request("complete"), MODEL)
                empty = (
                    client.complete(request("complete", "empty-candidates"), MODEL)
                    if os.getenv("ALEPH_ALPHA_EXAMPLE_REAL") != "1"
                    else None
                )
                return {
                    "native_type": type(result).__name__,
                    "empty_candidates": len(empty.completions)
                    if empty is not None
                    else "controlled-only",
                }
            if case == "embeddings":
                results = [
                    getattr(client, method)(request(method), MODEL)
                    for method in (
                        "embed",
                        "embeddings",
                        "semantic_embed",
                        "batch_semantic_embed",
                        "instructable_embed",
                    )
                ]
                return {
                    "native_types": [type(result).__name__ for result in results],
                    "semantic_dimensions": len(results[2].embedding),
                }
            return {
                "native_types": [
                    type(getattr(client, method)(request(method), MODEL)).__name__
                    for method in ("evaluate", "explain")
                ]
            }
        finally:
            client.session.close()


async def asynchronous(case, provider, host, token):
    async with AsyncClient(token=token, host=host, total_retries=0) as client:
        if case == "async-apis":
            results = []
            for method in (
                "chat",
                "complete",
                "embed",
                "semantic_embed",
                "batch_semantic_embed",
                "instructable_embed",
                "evaluate",
                "explain",
            ):
                result = await getattr(client, method)(request(method), MODEL)
                results.append(type(result).__name__)
            return {"native_types": results}
        if case == "async-streaming":
            results = []
            for method in ("complete_with_streaming", "chat_with_streaming"):
                items = [
                    item
                    async for item in getattr(client, method)(request(method), MODEL)
                ]
                results.append([type(item).__name__ for item in items])
            if os.getenv("ALEPH_ALPHA_EXAMPLE_REAL") != "1":
                items = [
                    item
                    async for item in client.chat_with_streaming(
                        request("chat", "split-secret"), MODEL
                    )
                ]
                assert any(
                    "PRIVATE-FRAGMENT" in getattr(item, "content", "") for item in items
                )
            return {
                "native_item_types": results,
                "split_credentials": "returned intact, captured redacted",
            }
        if case == "privacy":
            carrier = context.attach(
                context.set_value("respan_enable_content_tracing", False)
            )
            try:
                result = await client.complete(
                    request("complete", "PRIVATE-INITIAL"), MODEL
                )
                try:
                    await client.complete(
                        request("complete", "controlled-error PRIVATE-ERROR"), MODEL
                    )
                except ValueError:
                    pass
            finally:
                context.detach(carrier)
            stream = client.chat_with_streaming(request("chat", "PRIVATE-LATE"), MODEL)
            await anext(stream)
            carrier = context.attach(context.set_value("trace_content", False))
            context.detach(carrier)
            await stream.aclose()
            parent = provider.get_tracer("aleph_alpha_examples").start_span(
                "controlled_parent"
            )
            with trace.use_span(parent, end_on_exit=False):
                stream = client.chat_with_streaming(
                    request("chat", "PRIVATE-PARENT"), MODEL
                )
                await anext(stream)
            parent.set_attribute("respan_enable_content_tracing", False)
            parent.end()
            await stream.aclose()
            return {"native_type": type(result).__name__, "private_cases": 4}
        # Close before first pull; close after first native item; two pending
        # siblings under one parent; abandonment finalizes telemetry only.
        stream = client.chat_with_streaming(request("chat"), MODEL)
        await stream.aclose()
        stream = client.chat_with_streaming(request("chat"), MODEL)
        first = await stream.asend(None)
        await stream.aclose()
        with provider.get_tracer("aleph_alpha_examples").start_as_current_span(
            "controlled_siblings"
        ):
            a = client.chat_with_streaming(request("chat"), MODEL)
            b = client.chat_with_streaming(request("chat"), MODEL)
            await anext(a)
            await anext(b)
            await a.aclose()
            await b.aclose()
        stream = client.chat_with_streaming(request("chat"), MODEL)
        del stream
        gc.collect()
        return {"first_native_type": type(first).__name__, "lifecycle_cases": 5}


def run(case, provider):
    if case in {"chat", "completion", "embeddings", "evaluate-explain"}:
        return sync_case(case, provider)
    with host_context(case) as (host, token):
        return asyncio.run(asynchronous(case, provider, host, token))


SCENARIOS = {
    case: (lambda provider, case=case: run(case, provider))
    for case in (
        "chat",
        "completion",
        "embeddings",
        "async-streaming",
        "evaluate-explain",
        "privacy",
        "lifecycle",
        "async-apis",
    )
}
