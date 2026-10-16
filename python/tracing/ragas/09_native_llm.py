"""Controlled released Ragas APIs; provider calls are local unless explicitly exported."""

from __future__ import annotations

import os

os.environ["RAGAS_DO_NOT_TRACK"] = "true"
import asyncio

from _native_llm import generation_server
from _shared import run_case
from openai import AsyncOpenAI, OpenAI
from ragas.llms import llm_factory
from ragas.metrics import NumericMetric
from ragas.metrics.result import MetricResult


async def async_call(url, method):
    async with AsyncOpenAI(api_key="controlled", base_url=url, max_retries=0) as client:
        llm = llm_factory("controlled-metric", client=client)
        metric = NumericMetric(name="controlled_native_llm", prompt="Score {response}")
        return (
            await getattr(metric, method)(
                [{"response": "one"}, {"response": "two"}], llm=llm
            )
            if "batch" in method
            else await metric.ascore(response="one", llm=llm)
        )


def action(provider, local):
    with generation_server() as (url, requests):
        for method in ["score", "ascore", "batch_score", "abatch_score"]:
            if method in ["ascore", "abatch_score"]:
                result = asyncio.run(async_call(url, method))
            else:
                with OpenAI(
                    api_key="controlled", base_url=url, max_retries=0
                ) as client:
                    llm = llm_factory("controlled-metric", client=client)
                    metric = NumericMetric(
                        name="controlled_native_llm", prompt="Score {response}"
                    )
                    result = (
                        getattr(metric, method)(
                            [{"response": "one"}, {"response": "two"}], llm=llm
                        )
                        if "batch" in method
                        else metric.score(response="one", llm=llm)
                    )
            values = result if "batch" in method else [result]
            assert all(
                type(v) is MetricResult and v.value == 0 and v.reason == ""
                for v in values
            )
        assert len(requests) == 6 and all(
            r["model"] == "controlled-metric" for r in requests
        )
    owned = [
        span
        for span in local.get_finished_spans()
        if span.name.startswith("ragas.metric")
    ]
    assert len(owned) == 4 and all(
        "gen_ai.request.model" not in span.attributes
        and "gen_ai.usage.total_tokens" not in span.attributes
        for span in owned
    )
    return "four real Ragas/OpenAI local HTTP methods, six native requests, value0/reason empty; task model/usage not guessed"


if __name__ == "__main__":
    run_case("ragas_native_llm", action)
