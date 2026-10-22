"""One-script example for AsyncPipeline.run_async."""

import asyncio

from _shared import configure_respan, finish_respan, print_result


def run_async_pipeline_run_example():
    respan = configure_respan("haystack-async-pipeline-run")
    try:
        try:
            from haystack import AsyncPipeline
        except ImportError:
            from haystack import Pipeline as AsyncPipeline
        from haystack import component

        async def run_pipeline():
            @component
            class AsyncEcho:
                @component.output_types(text=str)
                async def run_async(self, text: str) -> dict[str, str]:
                    return {"text": text.upper()}

                @component.output_types(text=str)
                def run(self, text: str) -> dict[str, str]:
                    return {"text": text.upper()}

            pipeline = AsyncPipeline()
            pipeline.add_component("echo", AsyncEcho())
            return await pipeline.run_async({"echo": {"text": "async haystack"}})

        result = asyncio.run(run_pipeline())
        print_result("AsyncPipeline.run_async", result)
        return result
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run_async_pipeline_run_example()
