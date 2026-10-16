from __future__ import annotations

from _shared import (
    embedding_model_name,
    example_attributes,
    finish_respan,
    make_client,
    make_custom_identifier,
    make_respan,
    print_result,
    print_start,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "embeddings"


@workflow(name=workflow_name(EXAMPLE_NAME))
def _embeddings_workflow(texts: list[str]) -> str:
    with make_client() as client:
        response = client.embeddings.create(
            model=embedding_model_name(),
            input=texts,
        )
        data = getattr(response, "data", None) or []
        first_embedding = getattr(data[0], "embedding", []) if data else []
        return (
            f"embedding_count={len(data)} embedding_dimensions={len(first_embedding)}"
        )


def run_embeddings() -> None:
    custom_identifier = make_custom_identifier(EXAMPLE_NAME)
    respan = make_respan(EXAMPLE_NAME, custom_identifier)
    text = ""

    try:
        with example_attributes(EXAMPLE_NAME, custom_identifier):
            print_start(EXAMPLE_NAME, custom_identifier)
            text = _embeddings_workflow(
                [
                    "Respan traces Together AI chat calls.",
                    "Embeddings retain complete vector data.",
                ]
            )
    finally:
        finish_respan(respan)

    print_result(EXAMPLE_NAME, custom_identifier, text)


if __name__ == "__main__":
    run_embeddings()
