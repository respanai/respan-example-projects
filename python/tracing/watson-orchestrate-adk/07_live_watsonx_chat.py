from __future__ import annotations

import os

from _shared import (
    create_respan,
    example_attributes,
    load_repo_env,
    marker_for,
    optional_env,
    workflow_name,
)
from ibm_watsonx_orchestrate.client.autodiscover.watsonx_ai.watsonx_ai_client import (
    WatsonxAIClient,
)
from respan import workflow

EXAMPLE_NAME = "live-watsonx-chat"


@workflow(name=workflow_name(EXAMPLE_NAME))
def live_watsonx_chat(prompt: str) -> dict:
    client = WatsonxAIClient(model=optional_env("WATSON_ORCHESTRATE_LLM_MODEL"))
    return client.generate_response(
        input=prompt,
        instructions="Answer in one concise sentence.",
    )


def main() -> None:
    load_repo_env()
    if os.getenv("RESPAN_WATSON_LIVE") != "1":
        print(
            "live Watson example skipped: set RESPAN_WATSON_LIVE=1 to opt in",
            flush=True,
        )
        return
    if not os.getenv("WATSONX_APIKEY") or not os.getenv("WATSONX_SPACE_ID"):
        print("live Watsonx chat skipped: WATSONX credentials absent", flush=True)
        return
    marker = marker_for(EXAMPLE_NAME)
    respan = create_respan(EXAMPLE_NAME, marker)
    try:
        with example_attributes(EXAMPLE_NAME, marker):
            result = live_watsonx_chat("Explain why tracing agent runs is useful.")
    finally:
        respan.shutdown()
    print({"example": EXAMPLE_NAME, "marker": marker, "result": result}, flush=True)


if __name__ == "__main__":
    main()
