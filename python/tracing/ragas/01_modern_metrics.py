"""Controlled released Ragas APIs; provider calls are local unless explicitly exported."""

from __future__ import annotations

import os

os.environ["RAGAS_DO_NOT_TRACK"] = "true"
import asyncio

from _shared import run_case
from ragas.metrics.collections import ExactMatch
from ragas.metrics.result import MetricResult


def action(provider, local):
    metric = ExactMatch()
    row = {"reference": "Paris", "response": "Rome"}
    result = metric.score(**row)
    assert type(result) is MetricResult and result.value == 0
    assert asyncio.run(metric.ascore(**row)).value == 0
    batch = metric.batch_score([row] * 75)
    async_batch = asyncio.run(metric.abatch_score([row] * 75))
    assert len(batch) == len(async_batch) == 75 and all(
        r.value == 0 for r in batch + async_batch
    )
    return "score/ascore and complete native 75-item batch_score/abatch_score"


if __name__ == "__main__":
    run_case("ragas_collections", action)
