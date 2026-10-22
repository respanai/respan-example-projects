from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

EXAMPLES = [
    "01_core.py",
    "02_streaming_async.py",
    "03_agent_research_tools.py",
    "04_expected_error.py",
]


def main() -> None:
    directory = Path(__file__).resolve().parent
    env = dict(os.environ)
    env.setdefault(
        "RESPAN_EXAMPLE_RUN_ID",
        f"otel2-exa-python-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
    )
    failures: list[str] = []
    print(f"RESPAN_EXAMPLE_RUN_ID={env['RESPAN_EXAMPLE_RUN_ID']}", flush=True)
    for script in EXAMPLES:
        result = subprocess.run(
            [sys.executable, str(directory / script)],
            cwd=directory,
            env=env,
            timeout=180,
            check=False,
        )
        if result.returncode:
            failures.append(f"{script}: exit {result.returncode}")
    if failures:
        raise SystemExit("; ".join(failures))


if __name__ == "__main__":
    main()
