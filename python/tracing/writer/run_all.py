from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

EXAMPLES = sorted(
    path.name for path in Path(__file__).resolve().parent.glob("[0-9][0-9]_*.py")
)


def run() -> None:
    here = Path(__file__).resolve().parent
    env = os.environ.copy()
    marker = env.get("RESPAN_EXAMPLE_RUN_ID") or "writer-local-run"
    env["RESPAN_EXAMPLE_RUN_ID"] = marker
    failures: list[str] = []
    for example in EXAMPLES:
        print(f"\n### running {example}", flush=True)
        try:
            result = subprocess.run(
                [sys.executable, str(here / example)],
                check=False,
                env=env,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"{example}: timeout")
            continue
        if result.returncode:
            failures.append(f"{example}: exit {result.returncode}")
    if failures:
        raise RuntimeError("; ".join(failures))
    print(f"marker={marker}")


if __name__ == "__main__":
    run()
