"""Run the committed Temporal runtime examples with one marker."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = sorted(Path(__file__).parent.glob("[0-9][0-9]_*.py"))


def main() -> int:
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID", "temporal-group-local")
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
                timeout=180,
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export",
        action="store_true",
        help="Send synthetic spans to Respan using .env credentials",
    )
    parser.add_argument(
        "--remote-address",
        help="Use this explicitly supplied Temporal server instead of the ephemeral local server",
    )
    args = parser.parse_args()
    if args.export:
        os.environ["RESPAN_EXAMPLE_EXPORT"] = "1"
    if args.remote_address:
        os.environ["TEMPORAL_EXAMPLE_REMOTE"] = "1"
        os.environ["TEMPORAL_ADDRESS"] = args.remote_address
    raise SystemExit(main())
