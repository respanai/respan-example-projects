"""Run real plugin entry-point/worker scenarios; export is explicit opt-in."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
SCENARIOS = (
    ("outcomes", "outcomes_case.py", 0, True, ()),
    ("expected-failure", "failure_case.py", 1, True, ()),
    ("privacy", "privacy_case.py", 1, False, ()),
    ("async", "async_case.py", 0, True, ("-p", "pytest_asyncio.plugin")),
    ("phases", "phases_case.py", 1, True, ()),
    ("collection", "collection_case.py", 2, True, ()),
    ("interruption", "interruption_case.py", 2, True, ()),
    ("workers", "workers_case.py", 0, True, ("-p", "xdist.plugin", "-n", "2")),
)


def main() -> int:
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID") or "pytest-" + uuid4().hex
    failures = []
    with tempfile.TemporaryDirectory() as directory:
        report_dir = os.getenv("RESPAN_EXAMPLE_REPORT_DIR") or directory
        for name, scenario, expected, capture, extra in SCENARIOS:
            env = {
                **os.environ,
                "PYTHONPATH": str(ROOT),
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                "RESPAN_EXAMPLE_RUN_ID": marker,
                "RESPAN_EXAMPLE_SCENARIO": name,
                "RESPAN_EXAMPLE_REPORT_DIR": report_dir,
                "RESPAN_PYTEST_WORKFLOW_NAME": "pytest_" + name,
            }
            command = [
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "_bootstrap",
                "-p",
                "respan_instrumentation_pytest.plugin",
                "--respan-tracing",
                "-q",
                "--tb=short",
                str(ROOT / "scenarios" / scenario),
                *extra,
            ]
            if not capture:
                command.append("--no-respan-capture-content")
            print(f"\n### {name} run_id={marker}", flush=True)
            try:
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=env,
                    timeout=float(os.getenv("RESPAN_EXAMPLE_TIMEOUT_SECONDS", "60")),
                    check=False,
                )
                if result.returncode != expected:
                    failures.append(
                        f"{name}: exit {result.returncode}, expected {expected}"
                    )
                reports = [
                    json.loads(p.read_text())
                    for p in Path(report_dir).glob(name + "-*.json")
                ]
                if not reports:
                    failures.append(f"{name}: missing actual span report")
                for report in reports:
                    assert report["run_id"] == marker
                    assert report["spans"]
                    ids = {s["span_id"] for s in report["spans"]}
                    assert all(
                        s["parent_span_id"] is None or s["parent_span_id"] in ids
                        for s in report["spans"]
                    )
                    if not capture:
                        assert "pytest-secret-must-not-export" not in json.dumps(report)
            except (subprocess.TimeoutExpired, AssertionError) as exc:
                failures.append(f"{name}: {type(exc).__name__}")
        if failures:
            print("Failures: " + "; ".join(failures), file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
