"""Run the complete dedicated Python Anthropic example set."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

EXAMPLES = (
    "01_basic.py",
    "02_streaming.py",
    "03_tool_round.py",
    "04_expected_error.py",
    "05_async.py",
    "06_privacy.py",
    "07_managed_sessions.py",
    "08_typed_parse.py",
    "09_live_provider.py",
)


def main() -> None:
    root = Path(__file__).resolve().parent
    os.environ.setdefault("RESPAN_EXAMPLE_RUN_ID", f"anthropic-{uuid4().hex}")
    for script in EXAMPLES:
        print(f"\n--- running {script} ---", flush=True)
        subprocess.run([sys.executable, str(root / script)], check=True)


if __name__ == "__main__":
    main()
