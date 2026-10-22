"""Chat model batch."""

from _shared import init_telemetry, message_text, tracing_config
from langchain_core.language_models.fake_chat_models import FakeListChatModel


def chat_model_batch() -> None:
    init_telemetry("langchain-chat-model-batch")
    model = FakeListChatModel(responses=["alpha", "beta", "gamma"])
    responses = model.batch(
        ["Return alpha.", "Return beta.", "Return gamma."],
        config=tracing_config("chat_model_batch", {"batch_size": 3}),
    )
    print([message_text(response) for response in responses])


if __name__ == "__main__":
    chat_model_batch()
