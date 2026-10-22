from _shared import (
    EMBED_MODEL,
    RERANK_MODEL,
    create_cohere_client,
    create_respan,
    install_cohere_stubs_if_needed,
    run_with_example_attributes,
)
from respan import workflow

WORKFLOW_NAME = "cohere_embed_rerank.workflow"

install_cohere_stubs_if_needed()
respan = create_respan("cohere-embed-rerank-example")
client = create_cohere_client()


@workflow(name=WORKFLOW_NAME)
def cohere_embed_rerank() -> dict[str, object]:
    documents = [
        "Respan records traces, spans, token usage, and metadata for AI systems.",
        "Cohere rerank helps order candidate documents by relevance to a query.",
        "Embedding models convert text into vectors for semantic search.",
    ]
    embed_response = client.embed(
        model=EMBED_MODEL,
        input_type="search_document",
        texts=documents,
        embedding_types=["float"],
    )
    rerank_response = client.rerank(
        model=RERANK_MODEL,
        query="Which document explains ranking search results?",
        documents=documents,
        top_n=2,
    )
    return {
        "embedding_count": len(embed_response.embeddings.float_),
        "top_rerank_indexes": [result.index for result in rerank_response.results],
    }


def main() -> None:
    try:
        output = run_with_example_attributes(
            respan,
            workflow_name=WORKFLOW_NAME,
            action=cohere_embed_rerank,
        )
        print(output)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
