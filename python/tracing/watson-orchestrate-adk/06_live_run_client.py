from __future__ import annotations

import os

from _shared import (
    create_respan,
    example_attributes,
    load_repo_env,
    marker_for,
    optional_env,
    require_env,
    workflow_name,
)
from ibm_watsonx_orchestrate_clients.chat.run_client import RunClient
from respan import workflow

EXAMPLE_NAME = "live-run-client"


@workflow(name=workflow_name(EXAMPLE_NAME))
def live_run_client(message: str) -> dict:
    client = RunClient(
        base_url=require_env("WATSON_ORCHESTRATE_BASE_URL"),
        api_key=require_env("WATSON_ORCHESTRATE_API_KEY"),
        is_local=optional_env("WATSON_ORCHESTRATE_IS_LOCAL") == "true",
        verify=optional_env("WATSON_ORCHESTRATE_VERIFY_SSL"),
    )
    return client.create_run(
        message=message,
        agent_id=require_env("WATSON_ORCHESTRATE_AGENT_ID"),
        thread_id=optional_env("WATSON_ORCHESTRATE_THREAD_ID"),
        capture_logs=True,
    )


def main() -> None:
    load_repo_env()
    if os.getenv("RESPAN_WATSON_LIVE") != "1":
        print(
            "live Watson example skipped: set RESPAN_WATSON_LIVE=1 to opt in",
            flush=True,
        )
        return
    required = (
        "WATSON_ORCHESTRATE_BASE_URL",
        "WATSON_ORCHESTRATE_API_KEY",
        "WATSON_ORCHESTRATE_AGENT_ID",
    )
    if not all(os.getenv(name) for name in required):
        print("live Watson run skipped: service credentials absent", flush=True)
        return
    marker = marker_for(EXAMPLE_NAME)
    respan = create_respan(EXAMPLE_NAME, marker)
    try:
        with example_attributes(EXAMPLE_NAME, marker):
            result = live_run_client("Return one concise traced response.")
    finally:
        respan.shutdown()
    print({"example": EXAMPLE_NAME, "marker": marker, "result": result}, flush=True)


if __name__ == "__main__":
    main()
