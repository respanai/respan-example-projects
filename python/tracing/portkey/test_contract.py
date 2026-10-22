from __future__ import annotations

import ast
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import _shared
import pytest
import run_all

EXAMPLE_DIR = Path(__file__).resolve().parent


def test_roots_accept_semantic_inputs():
    for script in run_all.SCRIPTS:
        module = ast.parse((EXAMPLE_DIR / script).read_text())
        for node in ast.walk(module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                isinstance(d, ast.Call)
                and isinstance(d.func, ast.Name)
                and d.func.id == "workflow"
                for d in node.decorator_list
            ):
                assert len(node.args.args) == 1
                assert node.args.args[0].arg in {"prompt", "city", "values"}


def test_exact_marker_survives_dotenv(monkeypatch):
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "shell-marker")

    def fake_load(path, *, override):
        assert override is False
        os.environ.setdefault("RESPAN_EXAMPLE_RUN_ID", "dotenv-marker")

    monkeypatch.setattr(_shared, "load_dotenv", fake_load)
    _shared.load_root_env()
    assert _shared.marker() == "shell-marker"


def test_default_client_is_actual_sdk_fixture_and_ignores_live_key(monkeypatch):
    monkeypatch.setenv("PORTKEY_API_KEY", "must-not-be-used")
    client = _shared.make_client()
    try:
        assert client.api_key == "fixture"
        result = client.chat.completions.create(
            model="fixture-model", messages=[{"role": "user", "content": "hello"}]
        )
        assert result.choices[0].message.content == "Portkey response."
    finally:
        client.close()


def test_export_and_live_are_separate_opt_ins():
    source = (EXAMPLE_DIR / "_shared.py").read_text()
    assert "RESPAN_PORTKEY_EXPORT" in source and "RESPAN_PORTKEY_LIVE" in source
    assert "override=False" in source.replace(" ", "")
    assert "InMemorySpanExporter" in source and "finally:" in source
    assert (
        "respan-instrumentation-openinference"
        not in (EXAMPLE_DIR / "requirements.txt").read_text()
    )


def test_runner_continues_and_aggregates(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        name = Path(command[-1]).name
        calls.append(name)
        assert kwargs["env"]["RESPAN_EXAMPLE_RUN_ID"] == "runner-marker"
        if name == "timeout.py":
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        return SimpleNamespace(returncode=1 if name == "first.py" else 0)

    monkeypatch.setattr(run_all, "SCRIPTS", ("first.py", "timeout.py", "last.py"))
    monkeypatch.setattr(run_all.subprocess, "run", fake_run)
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "runner-marker")
    with pytest.raises(SystemExit) as caught:
        run_all.main()
    assert calls == [
        "first.py",
        "timeout.py",
        "last.py",
    ] and "first.py: exited 1" in str(caught.value)


def test_runner_complete_feature_set():
    assert len(run_all.SCRIPTS) == 13
    assert all((EXAMPLE_DIR / s).is_file() for s in run_all.SCRIPTS)
