from __future__ import annotations

from _shared import (
    create_respan,
    example_scope,
    finish_respan,
    provider_config,
    sync_client,
    workflow,
)
from openai import RateLimitError

SCENARIO = "expected-error"


def run_workflow(config) -> int:
    client = sync_client(config)

    @workflow(name="openlit_expected_error_workflow")
    def traced_workflow(expected_prompt: str) -> None:
        client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": expected_prompt}],
        )

    try:
        try:
            traced_workflow(expected_prompt="expected-rate-limit")
        except RateLimitError as error:
            if error.status_code != 429:
                raise
            return error.status_code
        raise RuntimeError("The deterministic OpenLIT error example did not fail.")
    finally:
        client.close()


def main() -> None:
    respan = create_respan(SCENARIO)
    try:
        with provider_config(force_mock=True) as config, example_scope(SCENARIO):
            print(f"{SCENARIO}: status={run_workflow(config)}", flush=True)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
