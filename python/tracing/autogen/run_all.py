"""Run every modern fixture example under one exact audit marker."""

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

SCRIPTS = (
    "01_assistant_run.py",
    "02_tool_use.py",
    "03_round_robin_team.py",
    "04_stream_lifecycle.py",
    "05_privacy_and_suppression.py",
    "06_agent_as_tool.py",
    "07_provider_error.py",
)


def main():
    env = os.environ.copy()
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", f"autogen-{uuid4().hex[:12]}")
    print("RESPAN_EXAMPLE_RUN_ID=" + env["RESPAN_EXAMPLE_RUN_ID"], flush=True)
    for script in SCRIPTS:
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / script)], env=env, check=True
        )
    print(f"Completed {len(SCRIPTS)} AutoGen fixture scripts.")


if __name__ == "__main__":
    main()
