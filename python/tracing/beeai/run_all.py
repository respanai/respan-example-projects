"""Run every BeeAI tracing example with one shared marker."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
EXAMPLES = (
    "01_requirement_agent.py",
    "02_chat_model.py",
    "03_tool_execution.py",
    "04_expected_error.py",
    "05_streaming.py",
    "06_embedding.py",
    "07_tool_calls.py",
    "08_workflow_structured.py",
    "09_privacy.py",
)


def main() -> None:
    env = os.environ.copy()
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", f"beeai-{uuid.uuid4().hex[:10]}")
    failures: list[str] = []
    for example in EXAMPLES:
        print(f"\n=== {example} ===", flush=True)
        result = subprocess.run(
            [sys.executable, str(EXAMPLE_DIR / example)],
            cwd=EXAMPLE_DIR,
            env=env,
            check=False,
        )
        if result.returncode:
            failures.append(example)
    if failures:
        raise SystemExit(f"BeeAI examples failed: {', '.join(failures)}")
    print(f"Completed {len(EXAMPLES)} BeeAI scenarios")
    print(f"RESPAN_EXAMPLE_RUN_ID={env['RESPAN_EXAMPLE_RUN_ID']}")


if __name__ == "__main__":
    main()
