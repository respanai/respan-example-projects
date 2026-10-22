"""Start opt-out and before-detach closed-parent veto under actual native tasks."""

import asyncio
import os

from _shared import FixtureLLM, Tracing, chat_context


async def main():
    tracing = Tracing("privacy-bounds")
    try:
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
        pause = asyncio.Event()
        stream = FixtureLLM(pause=pause).chat(chat_ctx=chat_context())
        await asyncio.sleep(0)
        os.environ["TRACELOOP_TRACE_CONTENT"] = "true"
        pause.set()
        assert (await stream.collect()).text == "native LiveKit output"
        pause = asyncio.Event()
        with tracing.provider.get_tracer("caller").start_as_current_span(
            "foreign-parent"
        ):
            stream = FixtureLLM(pause=pause).chat(chat_ctx=chat_context())
            await asyncio.sleep(0)
            os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
        os.environ["TRACELOOP_TRACE_CONTENT"] = "true"
        pause.set()
        assert (await stream.collect()).text == "native LiveKit output"
        # Parent created before activation cannot disclose its initial bound.
        tracing.owner.deactivate()
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
        with tracing.provider.get_tracer("caller").start_as_current_span(
            "preexisting-private-parent", attributes={"caller.field": "untouched"}
        ) as parent:
            original = dict(parent.attributes)
            tracing.owner.activate()
            os.environ["TRACELOOP_TRACE_CONTENT"] = "true"
            assert (
                await FixtureLLM().chat(chat_ctx=chat_context()).collect()
            ).text == ("native LiveKit output")
            assert dict(parent.attributes) == original
        spans = [
            s
            for s in tracing.exporter.get_finished_spans()
            if s.attributes.get("respan.entity.log_type") == "chat"
        ]
        assert len(spans) == 3
        assert all(
            not any(
                k in s.attributes
                for k in ["traceloop.entity.input", "traceloop.entity.output"]
            )
            for s in spans
        )
        assert all(s.attributes["gen_ai.usage.input_tokens"] == 11 for s in spans)
        print("three native privacy bounds remain closed; actual usage retained")
    finally:
        tracing.finish()


if __name__ == "__main__":
    asyncio.run(main())
