"""Controlled released Ragas APIs; provider calls are local unless explicitly exported."""

from __future__ import annotations

import os

os.environ["RAGAS_DO_NOT_TRACK"] = "true"
import numpy as np
from _shared import run_case
from ragas.metrics import numeric_metric
from ragas.metrics.result import MetricResult


def action(provider, local):
    expected = MetricResult(
        0,
        reason="",
        traces={
            "input": {
                "history": [
                    {"turn": n, "text": "Controlled history."} for n in range(75)
                ]
            },
            "output": {"vector": np.arange(5001), "flag": False, "empty": ""},
        },
    )

    @numeric_metric(name="complete_native_result")
    def metric(response):
        return expected

    assert metric.score(response="") is expected
    assert (
        expected.reason == ""
        and len(expected.traces["input"]["history"]) == 75
        and len(expected.traces["output"]["vector"]) == 5001
    )
    return "native MetricResult identity, full nested 75 history/5001 NumPy vector and false/zero/empty"


if __name__ == "__main__":
    run_case("ragas_complete_result", action)
