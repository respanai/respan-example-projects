"""Actual released Marqo clients; deterministic native HTTP by default."""

from _shared import marqo_client, run_case


def action(provider, local):
    with marqo_client() as (client, _requests):
        index = client.index("docs")
        docs = [
            {"_id": str(i), "text": "native", "flag": False, "vector": [0.0] * 5001}
            for i in range(75)
        ]
        index.add_documents(docs, tensor_fields=["text"], client_batch_size=30)
        index.update_documents(docs, client_batch_size=30)
        result = index.get_documents([str(i) for i in range(75)], expose_facets=True)
        assert (
            len(result["results"]) == 75 and len(result["results"][0]["vector"]) == 5001
        )
        assert index.get_document("doc", expose_facets=True)["flag"] is False
        index.delete_documents(["doc"])
    return "native threaded batches, full public75records/vectors and aggregate native results"


if __name__ == "__main__":
    run_case("marqo_documents", action)
