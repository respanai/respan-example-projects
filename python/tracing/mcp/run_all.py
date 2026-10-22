"""Run all local-protocol MCP scenarios with one exact Respan audit marker."""

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

SCRIPTS = (
    "01_tool_call_workflow.py",
    "02_resource_read_workflow.py",
    "03_prompt_fetch_workflow.py",
    "04_connection_failure_workflow.py",
    "05_client_input_continuation.py",
    "06_resource_prompt_continuations.py",
)


def main() -> None:
    directory = Path(__file__).resolve().parent
    env = os.environ.copy()
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", f"mcp-{uuid4().hex[:12]}")
    print(f"RESPAN_EXAMPLE_RUN_ID={env['RESPAN_EXAMPLE_RUN_ID']}", flush=True)
    for script in SCRIPTS:
        subprocess.run([sys.executable, str(directory / script)], env=env, check=True)
    print(f"Completed {len(SCRIPTS)} MCP scenarios.", flush=True)


if __name__ == "__main__":
    main()
