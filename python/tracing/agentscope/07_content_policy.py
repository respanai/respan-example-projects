"""Privacy snapshots, usage retention and standard OTel suppression."""

import asyncio
import os

from _fixtures import Fixture
from _shared import build_respan, example_scope
from agentscope.message import UserMsg
from opentelemetry import context
from opentelemetry.context import _SUPPRESS_INSTRUMENTATION_KEY
from respan import workflow
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


async def main():
    fixture = Fixture()
    respan = build_respan("content-policy", "agentscope_content_policy")

    @workflow(name="agentscope_content_policy")
    async def run(scenario):
        model = fixture.model()
        previous = os.environ.get("TRACELOOP_TRACE_CONTENT")
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
        pending = model([UserMsg(name="user", content="private fixture prompt")])
        if previous is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = previous
        await pending
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        try:
            await fixture.embedding()(["private fixture document"])
        finally:
            context.detach(token)
        token = context.attach(context.set_value(_SUPPRESS_INSTRUMENTATION_KEY, True))
        pending = model([UserMsg(name="user", content="suppressed fixture prompt")])
        context.detach(token)
        await pending
        return {"scenario": scenario, "private_calls": 2, "suppressed_calls": 1}

    with example_scope("content-policy"):
        try:
            print(await run("privacy and suppression"))
        finally:
            try:
                await fixture.close()
            finally:
                respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
