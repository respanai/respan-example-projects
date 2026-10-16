"""Actual released Marqo clients; deterministic native HTTP by default."""

from _shared import marqo_client, run_case


def action(provider, local):
    with marqo_client() as (client, _requests):
        result = client.create_index(
            "docs", model="actual-controlled-model", normalize_embeddings=False
        )
        assert result["acknowledged"]
        index = client.index("docs")
        docs = [
            {"_id": str(i), "text": "native", "flag": False, "zero": 0, "empty": ""}
            for i in range(75)
        ]
        written = index.add_documents(docs, tensor_fields=["text"])
        assert len(written["items"]) == 75 and written["errors"] is False
        result = index.search(q="native", limit=75, show_highlights=False)
        assert len(result["hits"]) == 75
        assert index.delete()["acknowledged"]
    return "native create/write/search/delete, full75records, false0empty"


if __name__ == "__main__":
    run_case("marqo_lifecycle", action)
