"""Controlled released Ragas APIs; provider calls are local unless explicitly exported."""

from __future__ import annotations

import os

os.environ["RAGAS_DO_NOT_TRACK"] = "true"
import asyncio
import types

import ragas
from _shared import run_case
from ragas import EvaluationDataset
from ragas.executor import Executor
from ragas.metrics import ExactMatch as LegacyExactMatch


def action(provider, local):
    dataset = EvaluationDataset.from_list(
        [{"response": "a", "reference": "a"}, {"response": "b", "reference": "a"}]
    )
    for mode in ["results", "aresults", "cancel"]:
        before = len(local.get_finished_spans())
        executor = ragas.evaluate(
            dataset,
            metrics=[LegacyExactMatch()],
            return_executor=True,
            show_progress=False,
        )
        assert type(executor) is Executor and len(local.get_finished_spans()) == before
        if mode == "results":
            assert executor.results() == [1.0, 0.0]
        elif mode == "aresults":
            assert asyncio.run(executor.aresults()) == [1.0, 0.0]
        else:
            assert executor.cancel() is None and executor.is_cancelled()
            for job in executor.jobs:
                if type(job[0]) is types.CoroutineType:
                    job[0].close()
    return (
        "original lazy Executor results/aresults/cancel; no invented cancelled output"
    )


if __name__ == "__main__":
    run_case("ragas_deferred", action)
