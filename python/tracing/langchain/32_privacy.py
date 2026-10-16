"""Environment start upper bound and Respan context end veto."""

import os

from _shared import init_telemetry, tracing_config
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def main():
    init_telemetry("langchain-privacy")
    old = os.environ.get("TRACELOOP_TRACE_CONTENT")
    try:
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
        assert (
            RunnableLambda(lambda x: x).invoke(
                "PRIVATE_START", config=tracing_config("privacy_start")
            )
            == "PRIVATE_START"
        )
        os.environ["TRACELOOP_TRACE_CONTENT"] = "true"

        iterator = FakeListChatModel(responses=["PRIVATE_END"]).stream(
            "PRIVATE_PROMPT", config=tracing_config("privacy_end")
        )
        first = next(iterator)
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        try:
            assert (
                first.content + "".join(chunk.content for chunk in iterator)
                == "PRIVATE_END"
            )
        finally:
            context.detach(token)
    finally:
        if old is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = old
    print("Private native results preserved.")


if __name__ == "__main__":
    main()
