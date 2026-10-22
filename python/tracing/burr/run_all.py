"""Run every Burr tracing example with one shared marker."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
EXAMPLES = (
    "01_counter_workflow.py",
    "02_expected_error.py",
    "03_custom_span_workflow.py",
    "04_streaming_workflow.py",
    "05_async_workflow.py",
    "06_state_schema_and_arguments.py",
    "07_private_error.py",
    "08_async_stream_and_builder.py",
    "09_iterate_and_step.py",
)


def main() -> None:
    env = os.environ.copy()
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", f"burr-{uuid.uuid4().hex[:10]}")
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
        raise SystemExit(f"Burr examples failed: {', '.join(failures)}")
    print(f"RESPAN_EXAMPLE_RUN_ID={env['RESPAN_EXAMPLE_RUN_ID']}")


if __name__ == "__main__":
    main()
