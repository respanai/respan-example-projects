"""Run every committed LlamaIndex example with one exact marker."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = sorted(path for path in Path(__file__).parent.glob("[0-9][0-9]_*.py"))


def main() -> int:
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID", "llama-index-group-local")
    environment = {
        **os.environ,
        "RESPAN_EXAMPLE_RUN_ID": marker,
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    failures: list[str] = []
    for script in SCRIPTS:
        try:
            completed = subprocess.run(
                [sys.executable, str(script)],
                cwd=script.parent,
                env=environment,
                timeout=90,
                check=False,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"{script.name}:timeout")
            continue
        if completed.returncode:
            failures.append(f"{script.name}:{completed.returncode}")
    print(f"RESPAN_EXAMPLE_RUN_ID={marker}")
    if failures:
        print("failures:", ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
