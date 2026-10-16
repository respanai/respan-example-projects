"""Run actual released SDK examples and inspect their native OTel spans."""

import json
import os
import subprocess
import sys
from pathlib import Path


def test_actual_examples_full_payloads_errors_privacy_and_connected_trees(tmp_path):
    root = Path(__file__).resolve().parent
    env = {
        **os.environ,
        "RESPAN_EXAMPLE_EXPORT": "0",
        "RESPAN_EXAMPLE_RUN_ID": "replicate-contract",
        "RESPAN_EXAMPLE_REPORT_DIR": str(tmp_path),
    }
    result = subprocess.run(
        [sys.executable, str(root / "run_all.py")],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    reports = {
        path.stem: json.loads(path.read_text()) for path in tmp_path.glob("*.json")
    }
    assert len(reports) == 9
    assert sum(len(report["spans"]) for report in reports.values()) == 45
    for report in reports.values():
        assert report["run_id"] == "replicate-contract"
        spans = report["spans"]
        assert len({span["trace_id"] for span in spans}) == 1
        ids = {span["span_id"] for span in spans}
        assert all(
            span["parent_span_id"] is None or span["parent_span_id"] in ids
            for span in spans
        )
        assert sum(span["parent_span_id"] is None for span in spans) == 1
    vector = reports["full_payloads"]["spans"][0]["attributes"]
    assert len(json.loads(vector["traceloop.entity.output"])) == 5001
    assert (
        len(json.loads(vector["traceloop.entity.input"])["kwargs"]["input"]["messages"])
        == 75
    )
    assert "controlled-secret" not in json.dumps(vector)
    assert (
        len(
            json.loads(
                reports["streaming"]["spans"][0]["attributes"][
                    "traceloop.entity.output"
                ]
            )
        )
        == 251
    )
    errors = reports["provider_errors"]["spans"][:2]
    assert [span["attributes"]["http.response.status_code"] for span in errors] == [
        429,
        201,
    ]
    assert all(
        span["status"] == "ERROR"
        and "traceloop.entity.output" not in span["attributes"]
        for span in errors
    )
    private = reports["privacy"]["spans"][:2]
    assert all(
        "traceloop.entity.input" not in span["attributes"]
        and "traceloop.entity.output" not in span["attributes"]
        for span in private
    )
    assert "PRIVATE" not in json.dumps(private)
