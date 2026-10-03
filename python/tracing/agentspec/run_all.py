"""Run every deterministic AgentSpec example under one exact audit marker."""

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if __name__ == "__main__":
    env = os.environ.copy()
    env.setdefault(
        "RESPAN_EXAMPLE_RUN_ID",
        datetime.now(timezone.utc).strftime("agentspec-%Y%m%d-%H%M%S"),
    )
    scripts = sorted(Path(__file__).parent.glob("[0-9][0-9]_*.py"))
    failed = []
    for script in scripts:
        result = subprocess.run(
            [sys.executable, str(script)], env=env, timeout=90, check=False
        )
        if result.returncode:
            failed.append(script.name)
    print(
        {
            "run_id": env["RESPAN_EXAMPLE_RUN_ID"],
            "scripts": len(scripts),
            "failed": failed,
        }
    )
    raise SystemExit(bool(failed))
