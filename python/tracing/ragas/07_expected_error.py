"""Controlled released Ragas APIs; provider calls are local unless explicitly exported."""

from __future__ import annotations

import os

os.environ["RAGAS_DO_NOT_TRACK"] = "true"
from _shared import run_case
from ragas.metrics import numeric_metric
from ragas.metrics.collections import StringPresence
from ragas.metrics.result import MetricResult


def action(provider, local):
    try:
        StringPresence().score(reference=1, response="Controlled native SDK error.")
    except AssertionError:
        pass
    else:
        raise AssertionError("native SDK validation error missing")

    @numeric_metric(name="caught_application_error")
    def metric(response):
        raise RuntimeError("Controlled application callback failure.")

    result = metric.score(response="Controlled caught callback.")
    assert (
        type(result) is MetricResult
        and result.value is None
        and "Controlled application callback failure." in result.reason
    )
    return "native AssertionError and native caught-callback MetricResult(value=None) outcome"


if __name__ == "__main__":
    run_case("ragas_expected_errors", action)
