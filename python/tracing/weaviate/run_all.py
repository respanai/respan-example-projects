"""Run every controlled scenario; real service access is a separate opt-in."""

import os
import subprocess
import sys
from pathlib import Path

EXAMPLES = [p.name for p in sorted(Path(__file__).parent.glob("0[1-8]_*.py"))]


def run():
    here = Path(__file__).resolve().parent
    env = os.environ.copy()
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", "weaviate-local-run")
    failures = []
    for name in EXAMPLES:
        try:
            result = subprocess.run(
                [sys.executable, str(here / name)], env=env, check=False, timeout=120
            )
        except subprocess.TimeoutExpired:
            failures.append(name + ": timeout")
            continue
        if result.returncode:
            failures.append(name + ": failed")
    if failures:
        raise RuntimeError("; ".join(failures))


if __name__ == "__main__":
    run()
