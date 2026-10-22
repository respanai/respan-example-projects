"""Actual released Marqo clients; deterministic native HTTP by default."""

import json

from _shared import marqo_client, run_case


def action(provider, local):
    with marqo_client() as (client, _requests):
        result = client.index("docs").embed(["native", ""], content_type=None)
    span = local.get_finished_spans()[-1]
    assert json.loads(span.attributes["traceloop.entity.output"]) == [
        result["embeddings"][0]["embedding"]
    ]
    assert len(result["embeddings"][0]["embedding"]) == 5001
    assert span.attributes["gen_ai.request.model"] == result["model"]
    assert "gen_ai.usage.input_tokens" not in span.attributes
    return "actual embedding5001 values, model/envelope false0empty, no guessed usage"


if __name__ == "__main__":
    run_case("marqo_embeddings", action)
