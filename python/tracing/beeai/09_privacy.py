"""Start-disabled capture and a late environment veto keep payloads out."""

import asyncio
import os

from _shared import create_respan, example_attributes, get_chat_model
from respan import workflow

WORKFLOW_NAME = "BeeAI Privacy Example"
respan = create_respan("beeai-privacy")
from beeai_framework.backend import UserMessage


@workflow(name=WORKFLOW_NAME)
async def privacy():
    old = os.environ.get("TRACELOOP_TRACE_CONTENT")
    try:
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
        run = get_chat_model().run([UserMessage("Private fixture input.")])

        async def allow_after_start(event, meta):
            os.environ["TRACELOOP_TRACE_CONTENT"] = "true"

        await run.on("start", allow_after_start)
        os.environ["TRACELOOP_TRACE_CONTENT"] = "true"
        run = get_chat_model().run([UserMessage("Private late-veto fixture input.")])

        async def deny_after_start(event, meta):
            os.environ["TRACELOOP_TRACE_CONTENT"] = "false"

        await run.on("success", deny_after_start)
    finally:
        if old is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = old


async def main():
    try:
        with example_attributes(WORKFLOW_NAME):
            await privacy()
    finally:
        respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
