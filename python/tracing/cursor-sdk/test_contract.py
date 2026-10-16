from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import run_all


def test_runner_maps_every_numbered_script():
    assert run_all.EXAMPLES == [
        p.name for p in sorted(Path(__file__).parent.glob("[0-9][0-9]_*.py"))
    ]
    assert len(run_all.EXAMPLES) == 11


def test_runner_aggregates_exit_timeout_and_preserves_marker(monkeypatch):
    calls = []

    def run(args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 2:
            raise subprocess.TimeoutExpired(args, 90)
        return subprocess.CompletedProcess(args, 1 if len(calls) == 1 else 0)

    monkeypatch.setattr(run_all.subprocess, "run", run)
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "contract-marker")
    assert run_all.main() == 1
    assert len(calls) == 11
    assert all(
        c["env"]["RESPAN_EXAMPLE_RUN_ID"] == "contract-marker" and c["timeout"] == 90
        for c in calls
    )


@pytest.mark.parametrize(
    "name,expected",
    [
        ("beforeSubmitPrompt", {"continue": True}),
        ("preToolUse", {"permission": "allow"}),
        ("beforeReadFile", {"permission": "allow"}),
        ("subagentStart", {"permission": "allow"}),
    ],
)
def test_real_cli_json_stdout_with_trace_disabled(name, expected):
    env = os.environ.copy()
    env["TRACE_TO_RESPAN"] = "off"
    response = subprocess.run(
        [sys.executable, "-m", "respan_instrumentation_cursor_sdk"],
        input=json.dumps({"hook_event_name": name}),
        text=True,
        capture_output=True,
        timeout=20,
        env=env,
        check=True,
    )
    assert json.loads(response.stdout) == expected
