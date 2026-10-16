"""Retriever error."""

from _shared import init_telemetry, tracing_config
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


class FailingRetriever(BaseRetriever):
    def _get_relevant_documents(
        self, query: str, *, run_manager=None
    ) -> list[Document]:
        raise RuntimeError(f"retriever failed for {query}")


def retriever_error() -> None:
    init_telemetry("langchain-retriever-error")
    retriever = FailingRetriever()
    try:
        retriever.invoke("missing", config=tracing_config("retriever_error"))
    except RuntimeError as exc:
        print(f"caught: {exc}")


if __name__ == "__main__":
    retriever_error()
