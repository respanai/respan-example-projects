"""Run all deterministic Agent Framework examples with one exact marker."""

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

SCRIPTS = (
    "01_agent_tool_workflow.py",
    "02_deterministic_failure.py",
    "04_stream_lifecycle.py",
    "05_content_privacy.py",
    "06_falsy_tools.py",
    "07_scoped_suppression.py",
    "08_embeddings.py",
)


def main():
    env = os.environ.copy()
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", f"maf-{uuid4().hex[:12]}")
    print("RESPAN_EXAMPLE_RUN_ID=" + env["RESPAN_EXAMPLE_RUN_ID"], flush=True)
    for script in SCRIPTS:
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / script)], env=env, check=True
        )
    print(
        f"Completed {len(SCRIPTS)} deterministic Microsoft Agent Framework scripts.",
        flush=True,
    )


if __name__ == "__main__":
    main()
