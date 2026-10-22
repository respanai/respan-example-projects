from __future__ import annotations

import ast
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import _shared
import pytest
import run_all


def test_requirements_are_released_and_native_extra_is_explicit():
    lines = (Path(__file__).parent / "requirements.txt").read_text().splitlines()
    assert "openrouter>=1.3.22,<2.0.0" in lines
    assert "openai>=3.0.0,<4.0.0" in lines
    assert "respan-instrumentation-openrouter[native]>=0.1.0" in lines
    assert not any(line.startswith("-e") for line in lines)


def test_env_preserves_shell_marker(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("RESPAN_EXAMPLE_RUN_ID=stale\n")
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "exact-marker")
    _shared._load_env_file(env)
    assert _shared.run_id() == "exact-marker"


def test_real_key_does_not_switch_fixture_transport(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "real-key-must-not-be-used")
    with _shared.native_client() as client:
        response = client.chat.send(
            model=_shared.MODEL, messages=[{"role": "user", "content": "hi"}]
        )
        assert response.id == "chatcmpl-p9-openrouter"


def test_live_is_explicit(monkeypatch):
    monkeypatch.delenv("OPENROUTER_EXAMPLE_LIVE", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "present-does-not-authorize-live")
    with pytest.raises(RuntimeError, match="OPENROUTER_EXAMPLE_LIVE"):
        _shared.native_client(live=True)


def test_runner_aggregates_failures_and_timeouts(monkeypatch):
    monkeypatch.setattr(run_all, "EXAMPLES", ["fail.py", "slow.py", "pass.py"])
    calls = []

    def fake(command, *, check, env, timeout):
        calls.append((env["RESPAN_EXAMPLE_RUN_ID"], timeout))
        if command[-1].endswith("slow.py"):
            raise subprocess.TimeoutExpired(command, timeout)
        return subprocess.CompletedProcess(
            command, 7 if command[-1].endswith("fail.py") else 0
        )

    monkeypatch.setattr(run_all.subprocess, "run", fake)
    with pytest.raises(RuntimeError, match="fail.py: exit 7; slow.py: timeout"):
        run_all.run()
    assert len(calls) == 3 and len({c[0] for c in calls}) == 1
    assert all(c[1] == 90 for c in calls)


def test_every_feature_script_has_a_bounded_workflow_root():
    for filename in run_all.EXAMPLES:
        tree = ast.parse((Path(__file__).parent / filename).read_text())
        functions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "run"
        ]
        assert len(functions) == 1, filename
        assert len(functions[0].args.args) == 1, filename
        assert functions[0].args.args[0].arg not in {"client", "model"}
    assert len(run_all.EXAMPLES) == 15


def test_metadata_uses_both_exact_markers():
    values = {}
    _shared.Tags("exact-marker", "contract").on_start(
        SimpleNamespace(set_attribute=lambda k, v: values.update({k: v}))
    )
    assert values["respan.metadata.run_id"] == "exact-marker"
    assert values["respan.metadata.example_run_id"] == "exact-marker"


def test_export_disabled_by_default(monkeypatch):
    monkeypatch.delenv("RESPAN_EXAMPLE_EXPORT", raising=False)
    monkeypatch.setenv("RESPAN_API_KEY", "key-presence-is-not-export-opt-in")
    monkeypatch.setattr(
        _shared,
        "RespanSpanExporter",
        lambda **kwargs: pytest.fail("unexpected trace exporter"),
    )
    with _shared.tracing("no_export"):
        assert os.environ["RESPAN_API_KEY"] == "key-presence-is-not-export-opt-in"
