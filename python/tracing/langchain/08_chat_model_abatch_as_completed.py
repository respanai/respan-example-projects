"""Chat model abatch_as_completed."""

import asyncio

from _shared import init_telemetry, message_text, tracing_config
from langchain_core.language_models.fake_chat_models import FakeChatModel


async def chat_model_abatch_as_completed() -> None:
    init_telemetry("langchain-chat-model-abatch-as-completed")
    model = FakeChatModel()
    completed = []
    async for index, response in model.abatch_as_completed(
        ["Return north.", "Return south."],
        config=tracing_config("chat_model_abatch_as_completed"),
    ):
        completed.append((index, message_text(response)))
    print(completed)


if __name__ == "__main__":
    asyncio.run(chat_model_abatch_as_completed())
