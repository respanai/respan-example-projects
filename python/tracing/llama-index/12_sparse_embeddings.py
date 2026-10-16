"""Run the released sparse-embedding base class with controlled full vectors."""

from _shared import create_respan, print_result, traced_example


def main() -> None:
    try:
        from llama_index.core.base.embeddings.base_sparse import BaseSparseEmbedding
    except ImportError:
        print_result("Skipped", "installed core has no sparse embedding surface")
        return

    class FixtureSparseEmbedding(BaseSparseEmbedding):
        model_name: str = "fixture-sparse-model"

        def _get_query_embedding(self, query: str) -> dict[int, float]:
            return {index: float(index) for index in range(256)}

        async def _aget_query_embedding(self, query: str) -> dict[int, float]:
            return self._get_query_embedding(query)

        def _get_text_embedding(self, text: str) -> dict[int, float]:
            return self._get_query_embedding(text)

        async def _aget_text_embedding(self, text: str) -> dict[int, float]:
            return self._get_query_embedding(text)

    context = create_respan(
        app_name="llama-index-sparse", example_name="12_sparse_embeddings"
    )
    with traced_example(
        context,
        root_span_name=context.example_name,
        input_data={"text": "controlled sparse text"},
    ) as root:
        vector = FixtureSparseEmbedding().get_text_embedding("controlled sparse text")
        assert len(vector) == 256
        root.set_output({"dimensions": len(vector)})
    print_result("Sparse dimensions", len(vector))


if __name__ == "__main__":
    main()
