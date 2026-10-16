"""Chat model batch_as_completed."""

from _shared import init_telemetry, message_text, tracing_config
from langchain_core.language_models.fake_chat_models import FakeListChatModel


def chat_model_batch_as_completed() -> None:
    init_telemetry("langchain-chat-model-batch-as-completed")
    model = FakeListChatModel(responses=["first", "second", "third"])
    completed = []
    for index, response in model.batch_as_completed(
        ["First", "Second", "Third"],
        config=tracing_config("chat_model_batch_as_completed"),
    ):
        completed.append((index, message_text(response)))
    print(completed)


if __name__ == "__main__":
    chat_model_batch_as_completed()
