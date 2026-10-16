"""Example environment and aggregate runner contract."""

import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace

EXAMPLE_DIR = Path(__file__).parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, EXAMPLE_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_environment_files_do_not_override_shell(monkeypatch):
    load("_fixture", "_fixture.py")
    shared = load("llama_shared_contract", "_shared.py")
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "shell-marker")
    calls = []
    monkeypatch.setattr(shared, "_env_paths_from", lambda **_: [Path(".env")])

    def read(_path, *, override):
        calls.append(override)
        if override:
            os.environ["RESPAN_EXAMPLE_RUN_ID"] = "dotenv-marker"

    monkeypatch.setattr(shared, "load_dotenv", read)
    shared._load_env_files()
    assert os.environ["RESPAN_EXAMPLE_RUN_ID"] == "shell-marker"
    assert calls == [False, False]


def test_fixture_default_ignores_credentials(monkeypatch):
    load("_fixture", "_fixture.py")
    shared = load("llama_shared_fixture_contract", "_shared.py")
    monkeypatch.delenv("RESPAN_LLAMA_INDEX_LIVE", raising=False)
    monkeypatch.setattr(
        shared,
        "_load_env_files",
        lambda: (_ for _ in ()).throw(
            AssertionError("fixture must not load credentials")
        ),
    )
    assert shared.load_gateway_settings().base_url == "https://fixture.invalid/v1"


def test_complete_runner_continues_and_aggregates(monkeypatch, capsys):
    runner = load("llama_runner_contract", "run_all.py")
    assert len(runner.SCRIPTS) == 12
    runner.SCRIPTS = [
        Path("01_success.py"),
        Path("02_failure.py"),
        Path("03_success.py"),
    ]
    calls = []

    def run(command, **_kwargs):
        calls.append(command[-1])
        return SimpleNamespace(returncode=2 if "failure" in command[-1] else 0)

    monkeypatch.setattr(runner.subprocess, "run", run)
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "runner-marker")
    assert runner.main() == 1
    assert len(calls) == 3
    assert "02_failure.py:2" in capsys.readouterr().out


def test_portable_requirements_and_explicit_shutdown():
    requirements = (EXAMPLE_DIR / "requirements.txt").read_text()
    assert "-e " not in requirements and "../" not in requirements
    shared = (EXAMPLE_DIR / "_shared.py").read_text()
    assert "context.respan.flush()" in shared
    assert "context.respan.shutdown()" in shared
