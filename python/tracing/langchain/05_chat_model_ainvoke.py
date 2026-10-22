"""Chat model ainvoke."""

import asyncio

from _shared import init_telemetry, message_text, tracing_config
from langchain_core.language_models.fake_chat_models import FakeChatModel


async def chat_model_ainvoke() -> None:
    init_telemetry("langchain-chat-model-ainvoke")
    model = FakeChatModel()
    response = await model.ainvoke(
        "Return a short async greeting.",
        config=tracing_config("chat_model_ainvoke"),
    )
    print(message_text(response))


if __name__ == "__main__":
    asyncio.run(chat_model_ainvoke())
