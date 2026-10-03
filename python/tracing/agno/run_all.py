"""Run the full suite with one exact audit marker and bounded execution."""

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

SCRIPTS = (
    "01_hello_world.py",
    "02_gateway.py",
    "03_tracing.py",
    "04_respan_params.py",
    "05_tool_use.py",
    "06_team.py",
    "07_streaming.py",
    "08_confirmation_and_error.py",
)


def main():
    env = os.environ.copy()
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", "agno-" + uuid4().hex[:12])
    env["AGNO_TELEMETRY"] = "false"
    failed = []
    for script in SCRIPTS:
        print(f"Running {script}", flush=True)
        try:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent / script)],
                env=env,
                check=False,
                timeout=120,
            )
            if result.returncode:
                failed.append(script)
        except subprocess.TimeoutExpired:
            failed.append(script)
    if failed:
        raise SystemExit("Failed Agno examples: " + ", ".join(failed))
    print("Completed Agno examples: " + env["RESPAN_EXAMPLE_RUN_ID"])


if __name__ == "__main__":
    main()
