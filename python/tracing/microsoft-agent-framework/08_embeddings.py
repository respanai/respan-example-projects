"""Capture full native embedding vectors, real usage fields, privacy and errors."""

import asyncio

from _shared import create_respan, finish_respan, workflow_attributes
from agent_framework import BaseEmbeddingClient, Embedding, GeneratedEmbeddings
from agent_framework.observability import EmbeddingTelemetryLayer
from opentelemetry import context
from respan import Respan, workflow
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY

WORKFLOW_NAME = "microsoft-agent-framework-embeddings"


class FixtureProvider(BaseEmbeddingClient):
    async def get_embeddings(self, values, *, options=None):
        if values == ["controlled-error"]:
            raise ValueError("Controlled embedding fixture error")
        return GeneratedEmbeddings(
            [Embedding([i / 128 for i in range(128)]) for _ in values],
            usage=None if values == ["no-usage"] else {"input_token_count": 5},
        )


class FixtureClient(EmbeddingTelemetryLayer, FixtureProvider):
    model = "respan-maf-embedding-fixture"
    OTEL_PROVIDER_NAME = "fixture"


@workflow(name=WORKFLOW_NAME)
async def run_example():
    client = FixtureClient()
    result = await client.get_embeddings(["embedding fixture"])
    assert len(result[0].vector) == 128
    no_usage = await client.get_embeddings(["no-usage"])
    assert no_usage.usage is None
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    try:
        await client.get_embeddings(["private embedding fixture"])
    finally:
        context.detach(token)
    try:
        await client.get_embeddings(["controlled-error"])
    except ValueError as exc:
        assert "Controlled embedding" in str(exc)
    else:
        raise AssertionError("Expected embedding failure")
    return {"dimensions": 128, "embedding_calls": 4, "controlled_error": True}


async def main():
    respan = create_respan(WORKFLOW_NAME)
    try:
        with Respan.propagate_attributes(**workflow_attributes(WORKFLOW_NAME)):
            print(await run_example())
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
