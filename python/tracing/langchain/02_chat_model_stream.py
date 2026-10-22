"""Chat model stream."""

from _shared import init_telemetry, message_text, tracing_config
from langchain_core.language_models.fake_chat_models import FakeListChatModel


def chat_model_stream() -> None:
    init_telemetry("langchain-chat-model-stream")
    model = FakeListChatModel(responses=["Streaming chat output."])
    chunks = [
        message_text(chunk)
        for chunk in model.stream(
            "Stream a short status update.",
            config=tracing_config("chat_model_stream"),
        )
    ]
    print("".join(chunks))


if __name__ == "__main__":
    chat_model_stream()
