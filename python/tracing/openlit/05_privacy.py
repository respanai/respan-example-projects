from __future__ import annotations

from _shared import (
    create_respan,
    example_scope,
    finish_respan,
    provider_config,
    sync_client,
    workflow,
)

SCENARIO = "privacy-opt-out"
PRIVATE_SENTINEL = "openlit-private-sentinel-do-not-export"


def run_workflow(config) -> None:
    client = sync_client(config)

    @workflow(name="openlit_privacy_opt_out_workflow")
    def traced_workflow(scenario_label: str) -> None:
        client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": scenario_label},
                {"role": "user", "content": PRIVATE_SENTINEL},
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "private_tool",
                        "description": PRIVATE_SENTINEL,
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            ],
        )

    try:
        traced_workflow(scenario_label="verify content capture opt out")
    finally:
        client.close()


def main() -> None:
    respan = create_respan(SCENARIO, capture_content=False)
    try:
        with provider_config(force_mock=True) as config, example_scope(SCENARIO):
            run_workflow(config)
            print(f"{SCENARIO}: completed without printing payloads", flush=True)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
