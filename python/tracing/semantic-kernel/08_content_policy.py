"""Environment/runtime privacy and standard OpenTelemetry suppression."""

import asyncio
import os
from pathlib import Path

from _shared import (
    close_kernel_clients,
    create_client,
    create_respan,
    example_attributes,
)
from opentelemetry import context
from opentelemetry.context import _SUPPRESS_INSTRUMENTATION_KEY
from respan import workflow
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAITextEmbedding,
)

SCRIPT_NAME = Path(__file__).name
APP_NAME = SCRIPT_NAME.removesuffix(".py")


async def private_call(mode: str):
    client = create_client()
    agent = ChatCompletionAgent(
        service=OpenAIChatCompletion(ai_model_id="fixture-model", async_client=client),
        name=f"Private_{mode}",
    )
    await agent.get_response(messages=f"private-{mode}-prompt")
    await OpenAITextEmbedding(
        ai_model_id="fixture-embedding", async_client=client
    ).generate_embeddings([f"private-{mode}-document"])


@workflow(name=SCRIPT_NAME)
async def run_content_policy(scenario: str) -> dict:
    previous = os.environ.get("TRACELOOP_TRACE_CONTENT")
    os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
    try:
        await private_call("environment")
    finally:
        if previous is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = previous
    for key, mode in [
        (ENABLE_CONTENT_TRACING_KEY, "context"),
        (_SUPPRESS_INSTRUMENTATION_KEY, "suppression"),
    ]:
        token = context.attach(context.set_value(key, mode == "suppression"))
        try:
            await private_call(mode)
        finally:
            context.detach(token)
    return {"scenario": scenario, "private_operations": 6, "suppressed_operations": 3}


async def main():
    respan = create_respan(APP_NAME)
    try:
        with example_attributes(APP_NAME):
            print(await run_content_policy("environment-context-suppression"))
    finally:
        try:
            await close_kernel_clients()
        finally:
            respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
