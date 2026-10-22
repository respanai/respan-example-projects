from __future__ import annotations

import json
import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

from _shared import require_run_id

EXAMPLES = (
    "01_sync_async.py",
    "02_streaming.py",
    "03_tool_calling.py",
    "04_expected_error.py",
    "05_privacy.py",
    "06_parsed_models.py",
    "07_full_tool_payloads.py",
    "08_parent_privacy.py",
    "09_raw_usage.py",
)
EXAMPLE_TIMEOUT_SECONDS = 60


def run_examples(
    run_id: str,
    *,
    base_dir: Path | None = None,
    python: str | None = None,
) -> list[str]:
    base_dir = base_dir or Path(__file__).resolve().parent
    python = python or sys.executable
    environment = dict(os.environ)
    environment["RESPAN_EXAMPLE_RUN_ID"] = run_id
    environment["PYTHONUNBUFFERED"] = "1"
    failures: list[str] = []
    for script_name in EXAMPLES:
        print(f"\n=== {script_name} marker={run_id} ===", flush=True)
        try:
            result = subprocess.run(
                [python, str(base_dir / script_name)],
                check=False,
                cwd=base_dir,
                env=environment,
                timeout=EXAMPLE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"{script_name}: timeout")
            continue
        if result.returncode:
            failures.append(f"{script_name}: exit {result.returncode}")
    return failures


def main() -> None:
    failures = run_examples(require_run_id())
    skipped = (
        ["06_parsed_models.py"]
        if tuple(int(part) for part in version("openlit").split(".")[:2]) < (1, 45)
        else []
    )
    report = {
        "total": len(EXAMPLES),
        "passed": len(EXAMPLES) - len(failures) - len(skipped),
        "failed": failures,
        "skipped": skipped,
        "feature_gates": "06 explicitly skips native Responses.parse under OpenLIT1.44",
    }
    print(json.dumps(report))
    if os.getenv("OPENLIT_RUNNER_REPORT"):
        Path(os.environ["OPENLIT_RUNNER_REPORT"]).write_text(
            json.dumps(report, indent=2)
        )
    if failures:
        for failure in failures:
            print(f"FAILED {failure}", file=sys.stderr, flush=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
