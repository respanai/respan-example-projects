from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

EXAMPLES = [p.name for p in sorted(Path(__file__).parent.glob("[0-9][0-9]_*.py"))]


def run():
    env = os.environ.copy()
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", f"otel2-openrouter-local-{time.time_ns()}")
    failures = []
    for filename in EXAMPLES:
        try:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent / filename)],
                check=False,
                env=env,
                timeout=90,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"{filename}: timeout")
        else:
            if result.returncode:
                failures.append(f"{filename}: exit {result.returncode}")
    if failures:
        raise RuntimeError("; ".join(failures))


if __name__ == "__main__":
    run()
