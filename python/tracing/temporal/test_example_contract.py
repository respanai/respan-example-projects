from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

EXAMPLE_DIR = Path(__file__).resolve().parent
SCRIPTS = sorted(EXAMPLE_DIR.glob("[0-9][0-9]_*.py"))


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_shell_marker_wins_over_dotenv(monkeypatch):
    shared = _load("temporal_example_shared_contract", EXAMPLE_DIR / "_shared.py")
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "shell-marker")
    monkeypatch.setenv("RESPAN_API_KEY", "test-key")
    monkeypatch.setattr(
        shared,
        "load_dotenv",
        lambda *_args, **_kwargs: os.environ.__setitem__(
            "RESPAN_EXAMPLE_RUN_ID", "dotenv-marker"
        ),
    )
    assert shared.marker() == "shell-marker"
    assert shared.temporal_id("case").startswith("shell-marker")


def test_all_examples_use_real_runtime_semantic_inputs_and_final_shutdown():
    assert len(SCRIPTS) == 4
    sources = [script.read_text() for script in SCRIPTS]
    assert all("create_environment(instrumentor)" in source for source in sources)
    assert all("finally:" in source for source in sources)
    assert all("finish_respan(respan)" in source for source in sources)
    assert '"Ada"' in sources[0]
    assert '"expected activity failure"' in sources[1]
    assert '"trace-release"' in sources[2]
    assert "Replayer(" in sources[2]
    assert "ENABLE_CONTENT_TRACING_KEY" in sources[3]
    assert "CancelledError" in sources[3]


def test_runner_continues_and_reports_aggregate_failures(monkeypatch, capsys):
    runner = _load("temporal_example_runner_contract", EXAMPLE_DIR / "run_all.py")
    runner.SCRIPTS = [Path("01_ok.py"), Path("02_bad.py"), Path("03_ok.py")]
    calls = []

    def run(command, **_kwargs):
        calls.append(command[-1])
        return SimpleNamespace(returncode=3 if command[-1].endswith("02_bad.py") else 0)

    monkeypatch.setattr(runner.subprocess, "run", run)
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "runner-marker")
    assert runner.main() == 1
    assert calls == ["01_ok.py", "02_bad.py", "03_ok.py"]
    output = capsys.readouterr().out
    assert "RESPAN_EXAMPLE_RUN_ID=runner-marker" in output
    assert "02_bad.py:3" in output


def test_requirements_are_registry_portable():
    requirements = (EXAMPLE_DIR / "requirements.txt").read_text()
    assert "-e " not in requirements
    assert "../../" not in requirements
    assert "respan-instrumentation-temporal>=0.1,<1" in requirements
