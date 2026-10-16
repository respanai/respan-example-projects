"""Controlled released Ragas APIs; provider calls are local unless explicitly exported."""

from __future__ import annotations

import os

os.environ["RAGAS_DO_NOT_TRACK"] = "true"
import asyncio

import ragas
from _shared import run_case
from ragas import EvaluationDataset
from ragas.dataset_schema import EvaluationResult
from ragas.metrics import ExactMatch as LegacyExactMatch


def action(provider, local):
    dataset = EvaluationDataset.from_list(
        [
            {"response": "Paris", "reference": "Paris"},
            {"response": "Rome", "reference": "Paris"},
        ]
    )
    sync = ragas.evaluate(dataset, metrics=[LegacyExactMatch()], show_progress=False)
    asynchronous = asyncio.run(
        ragas.aevaluate(dataset, metrics=[LegacyExactMatch()], show_progress=False)
    )
    assert type(sync) is type(asynchronous) is EvaluationResult
    assert (
        sync.scores
        == asynchronous.scores
        == [{"exact_match": 1.0}, {"exact_match": 0.0}]
    )
    assert len(sync.dataset) == 2
    return (
        "native typed evaluate/aevaluate results and connected legacy metric children"
    )


if __name__ == "__main__":
    run_case("ragas_evaluations", action)
