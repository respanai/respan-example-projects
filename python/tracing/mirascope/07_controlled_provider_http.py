"""Released OpenAI Completions/Responses and Mirascope2.5 XAI with mock HTTP."""

from __future__ import annotations

import asyncio
import json

from _controlled import openai_model
from _shared import create_respan, finish_respan, workflow_attributes
from respan import workflow


@workflow(name="mirascope-controlled-completions")
def completions():
    calls = 0
    for usage in (
        None,
        {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        {"prompt_tokens": True, "completion_tokens": -1, "total_tokens": False},
        {
            "prompt_tokens": 7,
            "completion_tokens": 3,
            "total_tokens": 10,
            "prompt_tokens_details": {"cached_tokens": 2, "cache_write_tokens": 4},
            "completion_tokens_details": {"reasoning_tokens": 1},
        },
    ):
        native, provider, requests = openai_model(usage=usage)
        try:
            assert (
                native.call("controlled native HTTP").text() == "actual provider result"
            )
            assert requests
            calls += 1
        finally:
            provider._completions_provider.client.close()
            provider._responses_provider.client.close()
    native, provider, _ = openai_model(
        stream=True,
        usage={"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
    )
    try:
        assert "actual streamed result" in "".join(
            native.stream("controlled stream HTTP").text_stream()
        )
    finally:
        provider._completions_provider.client.close()
    return {"calls": calls, "streams": 1, "paid_inference": False}


@workflow(name="mirascope-controlled-responses-xai")
async def responses():
    usage = {
        "input_tokens": 6,
        "output_tokens": 2,
        "total_tokens": 8,
        "input_tokens_details": {"cached_tokens": 1, "cache_write_tokens": 3},
        "output_tokens_details": {"reasoning_tokens": 2},
    }
    for xai in (False, True):
        native, provider, requests = openai_model(
            mode="responses", xai=xai, usage=usage
        )
        try:
            assert (
                await native.call_async("controlled Responses HTTP")
            ).text() == "actual provider result"
            assert requests
        finally:
            owner = provider if xai else provider._responses_provider
            await owner.async_client.close()
            owner.client.close()
    return {"responses": 1, "xai2_5": 1, "paid_inference": False}


async def main():
    runtime = create_respan("mirascope-controlled-provider-http")
    try:
        with runtime.propagate_attributes(
            **workflow_attributes("mirascope-controlled-completions", __file__)
        ):
            print(json.dumps(completions()))
        with runtime.propagate_attributes(
            **workflow_attributes("mirascope-controlled-responses-xai", __file__)
        ):
            print(json.dumps(await responses()))
    finally:
        finish_respan(runtime)


if __name__ == "__main__":
    asyncio.run(main())
