"""Explicit optional live provider call; controlled tests do not accept gateway routing."""

import asyncio
import os

from _pipeline import run
from _shared import ROOT, attributes, create_respan, finish_respan, marker, print_result
from dotenv import load_dotenv
from pipecat.services.openai.llm import OpenAILLMService
from respan import workflow


async def main():
    if os.getenv("RESPAN_PIPECAT_LIVE") != "1":
        print("SKIP live provider: set RESPAN_PIPECAT_LIVE=1 explicitly.")
        return
    load_dotenv(ROOT / ".env", override=False)
    if not os.getenv("PIPECAT_PROVIDER_API_KEY"):
        raise RuntimeError("PIPECAT_PROVIDER_API_KEY required for explicit live call")
    run_id = marker()
    sdk = create_respan("live-provider", run_id)

    @workflow(name="pipecat_live_provider")
    async def scenario(prompt):
        service = OpenAILLMService(
            api_key=os.environ["PIPECAT_PROVIDER_API_KEY"],
            base_url=os.getenv("PIPECAT_PROVIDER_BASE_URL"),
            settings=OpenAILLMService.Settings(
                model=os.getenv("PIPECAT_PROVIDER_MODEL", "gpt-4.1-nano")
            ),
        )
        try:
            collector, _worker = await run(
                service=service, messages=[{"role": "user", "content": prompt}]
            )
            return {
                "text": "".join(
                    f.text
                    for f in collector.frames
                    if type(f).__name__ == "LLMTextFrame"
                )
            }
        finally:
            await service._client.close()

    try:
        with attributes("live-provider", run_id):
            result = await scenario("Say a brief hello.")
        print_result("live-provider", result, run_id)
    finally:
        finish_respan(sdk)


if __name__ == "__main__":
    asyncio.run(main())
