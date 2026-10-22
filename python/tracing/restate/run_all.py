from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
SCRIPTS = [
    "01_workflow_success.py",
    "02_service_success.py",
    "03_expected_error.py",
    "04_object_replay_context.py",
    "05_custom_serde_privacy.py",
    "06_terminal_error.py",
]
TIMEOUT_SECONDS = 120


def main() -> None:
    env = dict(os.environ)
    env.setdefault(
        "RESPAN_EXAMPLE_RUN_ID",
        f"otel2-restate-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
    )
    failures: list[str] = []
    print(f"RESPAN_EXAMPLE_RUN_ID={env['RESPAN_EXAMPLE_RUN_ID']}", flush=True)
    for script in SCRIPTS:
        try:
            result = subprocess.run(
                [sys.executable, str(EXAMPLE_DIR / script)],
                cwd=EXAMPLE_DIR,
                env=env,
                timeout=TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"{script}: timed out")
            continue
        if result.returncode:
            failures.append(f"{script}: exit {result.returncode}")
    if failures:
        raise SystemExit("; ".join(failures))


if __name__ == "__main__":
    main()
