"""Run every mapped example with one marker and an aggregate failure result."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

EXAMPLES = sorted(Path(__file__).parent.glob("[0-9][0-9]_*.py"))


def main():
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID", "arize-controlled-local")
    failures = []
    for script in EXAMPLES:
        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                env={**os.environ, "RESPAN_EXAMPLE_RUN_ID": marker},
                cwd=script.parent,
                timeout=90,
                check=False,
            )
        except subprocess.TimeoutExpired:
            failures.append(script.name + ":timeout")
            continue
        if result.returncode:
            failures.append(script.name + ":" + str(result.returncode))
    print("RESPAN_EXAMPLE_RUN_ID=" + marker)
    if failures:
        print("Failed examples: " + ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
