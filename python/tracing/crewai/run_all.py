"""Run all CrewAI tracing examples in isolated Python processes."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
SCRIPTS = [
    "01_basic_crew.py",
    "02_tool_use.py",
    "03_attributes.py",
    "04_native_llm.py",
    "05_agent_methods.py",
    "06_flows.py",
    "07_privacy.py",
    "08_failures.py",
]


def main() -> None:
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID") or datetime.now(timezone.utc).strftime(
        "crewai-%Y%m%d-%H%M%S"
    )
    env = os.environ.copy()
    env["RESPAN_EXAMPLE_RUN_ID"] = run_id

    print(f"CrewAI example run id: {run_id}", flush=True)
    failures = []
    for script in SCRIPTS:
        print(f"\n== Running {script} ==", flush=True)
        try:
            result = subprocess.run(
                [sys.executable, str(EXAMPLE_DIR / script)],
                cwd=EXAMPLE_DIR,
                env=env,
                check=False,
                timeout=180,
            )
            if result.returncode:
                failures.append(f"{script}: exit {result.returncode}")
        except subprocess.TimeoutExpired:
            failures.append(f"{script}: timeout")
    if failures:
        raise SystemExit("; ".join(failures))
    print(f"completed={len(SCRIPTS)} marker={run_id}", flush=True)


if __name__ == "__main__":
    main()
