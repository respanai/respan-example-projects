"""Native sync/async Chat Completions, Responses, and streamed zero usage."""

import asyncio

from _fixtures import FixtureServer
from _shared import create_respan, run_with_attributes, shutdown_respan
from respan import workflow


@workflow(name="crewai_04_native_llm")
def run_native_llm(scenario: str) -> dict:
    outputs = {}
    for api in ("completions", "responses"):
        llm = FixtureServer().llm(api=api)
        outputs[f"{api}_sync"] = llm.call("Give a fixture answer.")
        outputs[f"{api}_async"] = asyncio.run(
            llm.acall("Give an async fixture answer.")
        )
    llm = FixtureServer().llm(stream=True)
    outputs["stream_sync"] = llm.call("Stream a fixture answer.")
    outputs["stream_async"] = asyncio.run(llm.acall("Stream an async fixture answer."))
    session = FixtureServer().llm().stream_events("Stream public lifecycle frames.")
    frames = list(session)
    outputs["public_stream_result"] = session.result
    outputs["public_stream_frame_count"] = len(frames)
    return {"scenario": scenario, "outputs": outputs}


def main():
    context = create_respan(
        app_name="crewai-04-native-llm",
        example_name="04_native_llm",
        workflow_name="crewai_04_native_llm",
    )
    try:
        print(
            run_with_attributes(context, lambda: run_native_llm("native-provider-apis"))
        )
    finally:
        shutdown_respan(context)


if __name__ == "__main__":
    main()
