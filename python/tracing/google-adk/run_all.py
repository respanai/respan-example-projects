"""Run every Google ADK tracing example with one audit marker."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

SCRIPTS = tuple(
    path.name for path in sorted(Path(__file__).parent.glob("[0-9][0-9]_*.py"))
)


def main() -> None:
    directory = Path(__file__).resolve().parent
    env = os.environ.copy()
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", f"google-adk-{uuid4().hex[:10]}")
    env.setdefault("RESPAN_ADK_MODEL_MODE", "local")
    print(f"RESPAN_EXAMPLE_RUN_ID={env['RESPAN_EXAMPLE_RUN_ID']}", flush=True)
    for script in SCRIPTS:
        subprocess.run(
            [sys.executable, str(directory / script)], env=env, check=True, timeout=120
        )


if __name__ == "__main__":
    main()
