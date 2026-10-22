"""Controlled released Ragas APIs; provider calls are local unless explicitly exported."""

from __future__ import annotations

import asyncio
import os

os.environ["RAGAS_DO_NOT_TRACK"] = "true"
from _shared import run_case
from opentelemetry import context
from ragas.metrics import numeric_metric
from ragas.metrics.collections import ExactMatch
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def action(provider, local):
    @numeric_metric(name="late_private_native")
    def metric(response):
        context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        return 0

    async def late_score():
        # The native sync score() owns a separate asyncio context. Await ascore
        # within one application scope so its late content veto bounds capture.
        scope = context.attach(context.get_current())
        try:
            result = await metric.ascore(response="private-controlled-late")
            assert result.value == 0
        finally:
            context.detach(scope)

    asyncio.run(late_score())
    with provider.get_tracer("ragas.examples").start_as_current_span(
        "private_application_parent", attributes={ENABLE_CONTENT_TRACING_KEY: False}
    ) as parent:
        parent.set_attribute(ENABLE_CONTENT_TRACING_KEY, True)
        assert (
            ExactMatch()
            .score(
                reference="private-controlled-ancestor",
                response="private-controlled-ancestor",
            )
            .value
            == 1
        )
    owned = [
        span
        for span in local.get_finished_spans()
        if span.name.startswith("ragas.metric")
    ]
    assert owned and all(
        "traceloop.entity.input" not in span.attributes
        and "traceloop.entity.output" not in span.attributes
        for span in owned
    )
    return "canonical late and initial ancestor content veto, unchanged native numeric results"


if __name__ == "__main__":
    run_case("ragas_content_policy", action)
