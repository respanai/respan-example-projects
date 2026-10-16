"""Controlled released Ragas APIs; provider calls are local unless explicitly exported."""

from __future__ import annotations

import os

os.environ["RAGAS_DO_NOT_TRACK"] = "true"
import asyncio

from _shared import run_case
from ragas.metrics import discrete_metric, numeric_metric, ranking_metric


def action(provider, local):
    @discrete_metric(name="future_discrete", allowed_values=["pass", "fail"])
    def discrete(response):
        return "pass"

    @numeric_metric(name="future_numeric")
    def numeric(response):
        return 0

    @ranking_metric(name="future_ranking", allowed_values=5001)
    def ranking(response):
        return list(range(5001))

    before = len(local.get_finished_spans())
    assert numeric(response="Controlled raw callback.") == 0
    assert len(local.get_finished_spans()) == before
    assert discrete.score(response="Controlled discrete.").value == "pass"
    assert numeric.score(response="Controlled numeric.").value == 0
    assert asyncio.run(numeric.ascore(response="Controlled async numeric.")).value == 0
    result = ranking.score(response="Controlled complete ranking.")
    assert result.value == list(range(5001))
    return "future decorators, untraced native raw callback, scored zero and full 5001 ranking"


if __name__ == "__main__":
    run_case("ragas_decorators", action)
