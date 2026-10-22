"""Run all deterministic Guardrails scenarios with one exact audit marker."""

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

SCRIPTS = (
    "01_pydantic_parse.py",
    "02_gateway_structured_generation.py",
    "03_propagated_attributes.py",
    "04_async_validation.py",
    "05_validator_outcomes.py",
    "06_streaming.py",
    "07_reask.py",
    "08_content_privacy.py",
    "09_controlled_error.py",
)


def main() -> None:
    env = os.environ.copy()
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", f"guardrails-{uuid4().hex[:12]}")
    print(f"RESPAN_EXAMPLE_RUN_ID={env['RESPAN_EXAMPLE_RUN_ID']}", flush=True)
    for script in SCRIPTS:
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / script)], env=env, check=True
        )
    print(f"Completed {len(SCRIPTS)} Guardrails scenarios.")


if __name__ == "__main__":
    main()
