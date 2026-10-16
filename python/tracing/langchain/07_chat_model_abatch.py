"""Chat model abatch."""

import asyncio

from _shared import init_telemetry, message_text, tracing_config
from langchain_core.language_models.fake_chat_models import FakeChatModel


async def chat_model_abatch() -> None:
    init_telemetry("langchain-chat-model-abatch")
    model = FakeChatModel()
    responses = await model.abatch(
        ["Return red.", "Return green."],
        config=tracing_config("chat_model_abatch", {"batch_size": 2}),
    )
    print([message_text(response) for response in responses])


if __name__ == "__main__":
    asyncio.run(chat_model_abatch())
