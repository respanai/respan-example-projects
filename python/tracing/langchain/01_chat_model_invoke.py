"""Chat model invoke."""

from _shared import init_telemetry, message_text, tracing_config
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage, SystemMessage


def chat_model_invoke() -> None:
    init_telemetry("langchain-chat-model-invoke")
    model = FakeListChatModel(responses=["Bonjour, Respan."])
    response = model.invoke(
        [
            SystemMessage(content="Translate English to French."),
            HumanMessage(content="Hello, Respan."),
        ],
        config=tracing_config("chat_model_invoke"),
    )
    print(message_text(response))


if __name__ == "__main__":
    chat_model_invoke()
