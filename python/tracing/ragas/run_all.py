"""Run every Ragas tracing example with one exact batch marker."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
SCRIPTS = (
    "01_modern_metrics.py",
    "02_evaluate.py",
    "03_experiment.py",
    "04_decorated_metrics.py",
    "05_deferred_executors.py",
    "06_complete_metric_result.py",
    "07_expected_error.py",
    "08_content_policy.py",
    "09_native_llm.py",
)


def main() -> None:
    env = os.environ.copy()
    env["RAGAS_DO_NOT_TRACK"] = "true"
    if "--export" in sys.argv:
        env["RESPAN_EXAMPLE_EXPORT"] = "1"
    run_id = env.get("RESPAN_EXAMPLE_RUN_ID") or datetime.now(timezone.utc).strftime(
        "ragas-suite-%Y%m%dT%H%M%SZ"
    )
    env["RESPAN_EXAMPLE_RUN_ID"] = run_id
    print(f"RESPAN_EXAMPLE_RUN_ID={run_id}", flush=True)

    failures: list[tuple[str, int]] = []
    for script in SCRIPTS:
        print(f"\n=== {script} ===", flush=True)
        result = subprocess.run(
            [sys.executable, str(EXAMPLE_DIR / script)],
            cwd=EXAMPLE_DIR,
            env=env,
            check=False,
        )
        print(f"PROCESS_EXIT script={script} code={result.returncode}", flush=True)
        if result.returncode:
            failures.append((script, result.returncode))

    if failures:
        rendered = ", ".join(f"{name} ({code})" for name, code in failures)
        raise SystemExit(f"Ragas example failures: {rendered}")


if __name__ == "__main__":
    main()
