from __future__ import annotations

import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import _shared
import pytest
import run_all

ROOT = Path(__file__).resolve().parent


def test_default_is_credential_free_and_explicit_export_preserves_marker(monkeypatch):
    captured = {}

    class FakeRespan:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.telemetry = SimpleNamespace(add_processor=lambda **kwargs: None)

    monkeypatch.setattr(_shared, "Respan", FakeRespan)
    monkeypatch.setenv("RESPAN_API_KEY", "synthetic-existing-key")
    monkeypatch.delenv("RESPAN_PIPECAT_EXPORT", raising=False)
    _shared.create_respan("fixture", "exact-marker")
    assert captured["api_key"] is None
    assert os.environ["RESPAN_API_KEY"] == "synthetic-existing-key"
    assert captured["metadata"]["run_id"] == "exact-marker"

    def dotenv(path, *, override):
        assert override is False
        os.environ.setdefault("RESPAN_EXAMPLE_RUN_ID", "dotenv-marker")

    monkeypatch.setattr(_shared, "load_dotenv", dotenv)
    monkeypatch.setenv("RESPAN_PIPECAT_EXPORT", "1")
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "shell-marker")
    _shared.create_respan("fixture", _shared.marker())
    assert captured["metadata"]["run_id"] == "shell-marker"


def test_runner_continues_and_aggregates_failures(monkeypatch):
    scripts = ("first.py", "timeout.py", "last.py")
    calls = []

    def run(command, **kwargs):
        script = Path(command[-1]).name
        calls.append(script)
        assert kwargs["env"]["RESPAN_EXAMPLE_RUN_ID"] == "runner-marker"
        if script == "timeout.py":
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        return SimpleNamespace(returncode=1 if script == "first.py" else 0)

    monkeypatch.setattr(run_all, "SCRIPTS", scripts)
    monkeypatch.setattr(run_all.subprocess, "run", run)
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "runner-marker")
    with pytest.raises(SystemExit) as error:
        run_all.main()
    assert calls == list(scripts)
    assert "first.py: exited 1" in str(error.value)
    assert "timeout.py: timed out" in str(error.value)


def test_runner_and_supported_native_worker_task_branches():
    assert set(run_all.SCRIPTS) == {p.name for p in ROOT.glob("[0-9][0-9]_*.py")}
    source = (ROOT / "_pipeline.py").read_text()
    assert "PipelineWorker" in source and "WorkerRunner" in source
    assert "PipelineTask" in source and "PipelineRunner" in source
    assert "settings=LLMSettings" in source


def test_live_provider_is_explicit_and_credentials_stay_outside_workflow():
    source = (ROOT / "02_gateway_llm_pipeline.py").read_text()
    assert "RESPAN_PIPECAT_LIVE" in source and "override=False" in source
    assert "async def scenario(prompt)" in source
    assert "PIPECAT_PROVIDER_API_KEY" in source
