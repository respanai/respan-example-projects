"""Runner and fixture configuration contracts; provider behavior uses real SDKs."""

import subprocess
from pathlib import Path

import _shared
import pytest
import run_all_examples


def test_runner_continues_after_exit_and_timeout_with_exact_marker(monkeypatch):
    calls = []

    def execute(command, **kwargs):
        name = Path(command[1]).name
        calls.append(name)
        assert kwargs["env"]["RESPAN_EXAMPLE_RUN_ID"] == "exact-marker"
        assert kwargs["timeout"] == 60
        if len(calls) == 1:
            return subprocess.CompletedProcess(command, 7)
        if len(calls) == 2:
            raise subprocess.TimeoutExpired(command, 60)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(run_all_examples.subprocess, "run", execute)
    assert run_all_examples.run_examples("exact-marker") == [
        "01_sync_async.py: exit 7",
        "02_streaming.py: timeout",
    ]
    assert calls == list(run_all_examples.EXAMPLES)


def test_dotenv_preserves_shell_marker(monkeypatch, tmp_path):
    path = tmp_path / ".env"
    path.write_text("RESPAN_EXAMPLE_RUN_ID=file-marker\n")
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "shell-marker")
    _shared._load_env_file(path)
    assert _shared.os.environ["RESPAN_EXAMPLE_RUN_ID"] == "shell-marker"


@pytest.mark.parametrize("marker", [" bad ", "bad\nmarker", "x" * 161])
def test_invalid_marker_rejected(monkeypatch, marker):
    monkeypatch.setattr(_shared, "RUN_ID", marker)
    with pytest.raises(RuntimeError, match="exact marker"):
        _shared.require_run_id()


def test_marker_metadata_is_exact(monkeypatch):
    monkeypatch.setattr(_shared, "RUN_ID", "exact-marker")
    metadata = _shared.example_metadata("controlled")
    assert metadata["run_id"] == metadata["example_run_id"] == "exact-marker"
    assert metadata["scenario"] == "controlled"


def test_flush_failure_still_shuts_down():
    calls = []

    class Telemetry:
        def flush(self):
            calls.append("flush")
            raise RuntimeError("controlled")

        def shutdown(self):
            calls.append("shutdown")

    with pytest.raises(RuntimeError, match="controlled"):
        _shared.finish_respan(Telemetry())
    assert calls == ["flush", "shutdown"]
