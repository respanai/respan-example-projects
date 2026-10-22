"""Run all maintained Instructor examples in isolated processes."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
SCRIPTS = [
    "01_create.py",
    "02_validation_hooks.py",
    "03_create_with_completion.py",
    "04_create_iterable.py",
    "05_async_create.py",
    "06_responses.py",
    "07_partial_stream.py",
    "08_controlled_errors.py",
    "09_privacy.py",
    "10_typed_dict.py",
    "11_async_stream_cancel.py",
]


def main() -> None:
    environment = dict(os.environ)
    environment.setdefault(
        "RESPAN_EXAMPLE_RUN_ID", "instructor-" + uuid.uuid4().hex[:12]
    )
    failures = []
    for script in SCRIPTS:
        print(f"\n== Running {script} ==", flush=True)
        result = subprocess.run(
            [sys.executable, str(EXAMPLE_DIR / script)],
            cwd=EXAMPLE_DIR,
            check=False,
            env=environment,
            timeout=90,
        )

        if result.returncode:
            failures.append(script)
    if failures:
        raise SystemExit(f"Failed scenarios: {failures}")


if __name__ == "__main__":
    main()
