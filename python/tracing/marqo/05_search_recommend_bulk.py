"""Actual released Marqo clients; deterministic native HTTP by default."""

from _shared import marqo_client, run_case


def action(provider, local):
    with marqo_client() as (client, _requests):
        index = client.index("docs")
        result = index.search(
            q={"native": 0.0},
            limit=75,
            offset=0,
            show_highlights=False,
            filter_string="flag:false",
        )
        assert len(result["hits"]) == 75
        assert index.recommend(["doc"], limit=0)["hits"] == []
        client.bulk_search([{"index": "docs", "q": "native", "limit": 0}])
    return (
        "native weighted/filter search, recommend and bulk typed request configuration"
    )


if __name__ == "__main__":
    run_case("marqo_search_queries", action)
