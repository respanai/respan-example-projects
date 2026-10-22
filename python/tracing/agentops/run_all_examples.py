"""Run every bounded fixture in a fresh process, reporting all failures."""

import json
import os
import subprocess
import sys
from pathlib import Path

EXAMPLES = (
    "01_decorator_hierarchy.py",
    "02_expected_failure.py",
    "03_async_decorators.py",
    "04_manual_metadata.py",
    "05_provider_calls_and_tools.py",
    "06_provider_stream_embeddings.py",
    "07_privacy.py",
    "08_guardrail.py",
    "09_generator_protocol.py",
)


def main():
    base = Path(__file__).resolve().parent
    failed = []
    for script in EXAMPLES:
        print(f"Running {script}", flush=True)
        result = subprocess.run([sys.executable, str(base / script)], check=False)
        if result.returncode:
            failed.append(script)
    report = {
        "total": len(EXAMPLES),
        "passed": len(EXAMPLES) - len(failed),
        "failed": failed,
        "skipped": [],
    }
    print(json.dumps(report))
    path = os.getenv("AGENTOPS_RUNNER_REPORT")
    if path:
        Path(path).write_text(json.dumps(report, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
