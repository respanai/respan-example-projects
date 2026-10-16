from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

EXAMPLES = [p.name for p in sorted(Path(__file__).parent.glob("[0-9][0-9]_*.py"))]


def main():
    here = Path(__file__).resolve().parent
    env = os.environ.copy()
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", "p10-cursor-" + str(time.time_ns()))
    failed = []
    for name in EXAMPLES:
        try:
            result = subprocess.run(
                [sys.executable, str(here / name)], env=env, timeout=90, check=False
            )
            if result.returncode:
                failed.append({"script": name, "exit_code": result.returncode})
        except subprocess.TimeoutExpired:
            failed.append({"script": name, "timeout": 90})
    print(
        {
            "total": len(EXAMPLES),
            "failed": failed,
            "run_id": env["RESPAN_EXAMPLE_RUN_ID"],
        }
    )
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
