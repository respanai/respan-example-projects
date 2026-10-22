"""Run the full Dify tracing example set in separate processes."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
SCRIPTS = [
    "01_chat_blocking.py",
    "02_chat_streaming.py",
    "03_completion.py",
    "04_workflow_and_api.py",
    "05_respan_context_and_files.py",
    "06_async_chat_and_workflow.py",
    "07_knowledge_workspace.py",
]


def main() -> None:
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID") or f"dify-py-{uuid.uuid4().hex[:12]}"
    child_env = {**os.environ, "RESPAN_EXAMPLE_RUN_ID": run_id}
    print(f"example_run_id={run_id}", flush=True)
    for script in SCRIPTS:
        print(f"\n### Running {script}", flush=True)
        subprocess.run(
            [sys.executable, script],
            cwd=EXAMPLE_DIR,
            env=child_env,
            check=True,
        )


if __name__ == "__main__":
    main()
