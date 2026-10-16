"""Run every Mirascope tracing example with one exact batch marker."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
SCRIPTS = (
    "01_call_and_tool.py",
    "02_sync_async_stream.py",
    "03_expected_error.py",
    "04_privacy.py",
    "05_live_gateway.py",
    "06_context_calls_and_toolkits.py",
    "07_controlled_provider_http.py",
    "08_complete_tools_and_history.py",
    "09_stream_errors_and_veto.py",
)


def main() -> None:
    env = os.environ.copy()
    env.setdefault(
        "RESPAN_EXAMPLE_RUN_ID",
        datetime.now(timezone.utc).strftime("mirascope-suite-%Y%m%dT%H%M%SZ"),
    )
    print(f"RESPAN_EXAMPLE_RUN_ID={env['RESPAN_EXAMPLE_RUN_ID']}", flush=True)
    failures: list[tuple[str, int]] = []
    for script in SCRIPTS:
        print(f"\n=== {script} ===", flush=True)
        result = subprocess.run(
            [sys.executable, str(EXAMPLE_DIR / script)],
            cwd=EXAMPLE_DIR,
            env=env,
            check=False,
        )
        print(f"exit_code={result.returncode} script={script}", flush=True)
        if result.returncode:
            failures.append((script, result.returncode))

    if failures:
        rendered = ", ".join(f"{script} ({code})" for script, code in failures)
        raise SystemExit(f"Mirascope example failures: {rendered}")


if __name__ == "__main__":
    main()
