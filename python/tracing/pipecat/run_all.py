"""Run every controlled scenario and the explicitly gated live example."""

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = (
    "01_offline_pipeline.py",
    "02_gateway_llm_pipeline.py",
    "03_expected_error.py",
    "04_native_http_service.py",
    "05_tools_and_history.py",
    "06_private_pipeline.py",
    "07_voice_frames.py",
    "08_native_cancel_and_partial_error.py",
    "09_ambient_supplied_parent.py",
)


def main():
    root = Path(__file__).resolve().parent
    env = os.environ.copy()
    env.setdefault(
        "RESPAN_EXAMPLE_RUN_ID",
        "pipecat-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    )
    failures = []
    for script in SCRIPTS:
        print("Running " + script, flush=True)
        try:
            result = subprocess.run(
                [sys.executable, str(root / script)], env=env, timeout=75, check=False
            )
            if result.returncode:
                failures.append(f"{script}: exited {result.returncode}")
        except subprocess.TimeoutExpired:
            failures.append(f"{script}: timed out")
    if failures:
        raise SystemExit("Failed: " + ", ".join(failures))
    print(
        "Completed Pipecat examples: RESPAN_EXAMPLE_RUN_ID="
        + env["RESPAN_EXAMPLE_RUN_ID"]
    )


if __name__ == "__main__":
    main()
