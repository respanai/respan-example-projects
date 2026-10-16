from __future__ import annotations

from _shared import (
    example_attributes,
    finish_respan,
    make_client,
    make_custom_identifier,
    make_respan,
    print_result,
    print_start,
    rerank_model_name,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "rerank"


@workflow(name=workflow_name(EXAMPLE_NAME))
def _rerank_workflow(query: str) -> str:
    with make_client() as client:
        response = client.rerank.create(
            model=rerank_model_name(),
            query=query,
            documents=[
                "Distributed tracing shows how requests move through services.",
                "Sourdough bread needs flour, water, salt, and patience.",
                "A beach umbrella blocks sunlight.",
            ],
            top_n=1,
            return_documents=True,
        )
        results = getattr(response, "results", None) or []
        if not results:
            return "no rerank results"
        top = results[0]
        return f"top_index={top.index} relevance_score={top.relevance_score}"


def run_rerank() -> None:
    custom_identifier = make_custom_identifier(EXAMPLE_NAME)
    respan = make_respan(EXAMPLE_NAME, custom_identifier)
    text = ""

    try:
        with example_attributes(EXAMPLE_NAME, custom_identifier):
            print_start(EXAMPLE_NAME, custom_identifier)
            text = _rerank_workflow("Which document is about observability?")
    finally:
        finish_respan(respan)

    print_result(EXAMPLE_NAME, custom_identifier, text)


if __name__ == "__main__":
    run_rerank()
