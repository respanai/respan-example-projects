"""Hello-world quickstart for Respan LangChain instrumentation.

Run:
    python 00_quickstart.py

The example uses a fake LangChain chat model, so it does not need an OpenAI key.
Set RESPAN_EXPORT=1 explicitly to export the controlled run to Respan.
"""

from __future__ import annotations

from _shared import init_telemetry, tracing_config
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage, SystemMessage


def langchain_instrumentation_quickstart() -> None:
    init_telemetry("langchain-quickstart")

    model = FakeListChatModel(responses=["Hello from a traced LangChain run."])
    response = model.invoke(
        [
            SystemMessage(content="Reply in one short sentence."),
            HumanMessage(content="Say hello to Respan tracing."),
        ],
        config=tracing_config("hello_world"),
    )
    print(response.content)


if __name__ == "__main__":
    langchain_instrumentation_quickstart()
