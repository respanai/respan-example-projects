import asyncio

from _http_service import ProviderService
from _pipeline import run
from _shared import attributes, create_respan, finish_respan, marker, print_result
from respan import workflow


async def main():
    run_id = marker()
    sdk = create_respan("native-http-service", run_id)

    @workflow(name="pipecat_native_http_service")
    async def scenario(prompt):
        service = ProviderService(
            api_key="fixture",
            settings=ProviderService.Settings(model="fixture-native-model"),
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
        with attributes("native-http-service", run_id):
            result = await scenario(
                "Use the native Pipecat OpenAI service over controlled HTTP/SSE."
            )
        print_result("native-http-service", result, run_id)
    finally:
        finish_respan(sdk)


if __name__ == "__main__":
    asyncio.run(main())
