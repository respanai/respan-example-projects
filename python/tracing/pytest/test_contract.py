"""Check real runner reports instead of source spelling."""

import json
import os
import subprocess
import sys
from pathlib import Path


def test_native_plugin_scenarios(tmp_path):
    root = Path(__file__).resolve().parent
    env = {
        **os.environ,
        "RESPAN_EXAMPLE_EXPORT": "0",
        "RESPAN_EXAMPLE_REPORT_DIR": str(tmp_path),
        "RESPAN_EXAMPLE_RUN_ID": "pytest-contract",
    }
    completed = subprocess.run(
        [sys.executable, str(root / "run_all.py")],
        env=env,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    reports = [json.loads(p.read_text()) for p in tmp_path.glob("*.json")]
    assert {r["scenario"] for r in reports} == {
        "outcomes",
        "expected-failure",
        "privacy",
        "async",
        "phases",
        "collection",
        "interruption",
        "workers",
    }
    assert len([r for r in reports if r["scenario"] == "workers"]) == 3
    assert all(r["span_count"] for r in reports)
