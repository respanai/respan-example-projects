"""Run every mapped fixture with one marker and bounded child processes."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
SCRIPTS = [
    "01_predict_signature.py",
    "02_chain_of_thought.py",
    "03_module_workflow.py",
    "04_tool_call.py",
    "05_react_agent.py",
    "06_evaluate_program.py",
    "07_async_calls.py",
    "08_privacy_and_errors.py",
    "09_embeddings.py",
    "10_native_requests_streams.py",
    "11_react_v2.py",
]


def main() -> int:
    env = dict(os.environ)
    env.setdefault(
        "RESPAN_EXAMPLE_RUN_ID",
        datetime.now(timezone.utc).strftime("dspy-%Y%m%dT%H%M%SZ"),
    )
    env.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
    failures = []
    for script in SCRIPTS:
        print(f"Running {script}", flush=True)
        try:
            result = subprocess.run(
                [sys.executable, script],
                cwd=EXAMPLE_DIR,
                env=env,
                check=False,
                timeout=240,
            )
            if result.returncode:
                failures.append(script)
        except subprocess.TimeoutExpired:
            failures.append(script)
    print(
        f"Completed {len(SCRIPTS) - len(failures)}/{len(SCRIPTS)} scripts; run_id={env['RESPAN_EXAMPLE_RUN_ID']}"
    )
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
