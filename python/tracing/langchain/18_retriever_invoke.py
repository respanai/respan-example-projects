"""Retriever invoke."""

from _shared import init_telemetry, tracing_config
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


class StaticRetriever(BaseRetriever):
    documents: list[Document]

    def _get_relevant_documents(
        self, query: str, *, run_manager=None
    ) -> list[Document]:
        matches = [
            document
            for document in self.documents
            if query.lower() in document.page_content.lower()
        ]
        return matches or self.documents[:1]


def retriever_invoke() -> None:
    init_telemetry("langchain-retriever-invoke")
    retriever = StaticRetriever(
        documents=[
            Document(page_content="Respan captures LangChain callback spans."),
            Document(
                page_content="Callbacks cover tools, chains, models, and retrievers."
            ),
        ]
    )
    documents = retriever.invoke(
        "callbacks",
        config=tracing_config("retriever_invoke"),
    )
    print([document.page_content for document in documents])


if __name__ == "__main__":
    retriever_invoke()
