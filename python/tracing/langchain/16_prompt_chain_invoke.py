"""Prompt chain invoke."""

from _shared import init_telemetry, tracing_config
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


def prompt_chain_invoke() -> None:
    init_telemetry("langchain-prompt-chain-invoke")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You write concise release notes."),
            ("human", "Summarize this change: {change}"),
        ]
    )
    model = FakeListChatModel(responses=["Added LangChain tracing examples."])
    chain = prompt | model | StrOutputParser()
    response = chain.invoke(
        {"change": "New numbered examples for callback coverage."},
        config=tracing_config("prompt_chain_invoke"),
    )
    print(response)


if __name__ == "__main__":
    prompt_chain_invoke()
