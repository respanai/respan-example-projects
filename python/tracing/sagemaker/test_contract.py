import json
import os
import subprocess
import sys
from pathlib import Path


def test_released_native_sdk_scenario_reports(tmp_path):
    root = Path(__file__).resolve().parent
    result = subprocess.run(
        [sys.executable, str(root / "run_all.py")],
        cwd=root,
        env={
            **os.environ,
            "RESPAN_EXAMPLE_EXPORT": "0",
            "RESPAN_EXAMPLE_REPORT_DIR": str(tmp_path),
            "RESPAN_EXAMPLE_RUN_ID": "sagemaker-contract",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    reports = [json.loads(p.read_text()) for p in tmp_path.glob("*.json")]
    assert len(reports) in (6, 7)
    assert all(r["run_id"] == "sagemaker-contract" and r["spans"] for r in reports)
    embedding = next(r for r in reports if r["scenario"] == "05_embedding")
    assert any(
        len(
            json.loads(
                s["attributes"].get("traceloop.entity.output", "null") or "null"
            )[0]
        )
        == 5001
        for s in embedding["spans"]
        if s["attributes"].get("respan.entity.log_type") == "embedding"
    )
