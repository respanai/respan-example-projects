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


def _workflow_signatures(filename: str) -> list[list[str]]:
    module = ast.parse((EXAMPLE_DIR / filename).read_text(encoding="utf-8"))
    return [
        [argument.arg for argument in node.args.args]
        for node in ast.walk(module)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and any(
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func.id == "workflow"
            for decorator in node.decorator_list
        )
    ]


def test_roots_accept_one_bounded_semantic_input():
    for script in (*run_all.SCRIPTS, run_all.LIVE_SCRIPT):
        assert len(_workflow_signatures(script)) == 1, script
        assert len(_workflow_signatures(script)[0]) == 1, script


def test_exact_marker_survives_dotenv(monkeypatch):
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "shell-marker")

    def fake_load(_path, *, override):
        assert override is False
        os.environ.setdefault("RESPAN_EXAMPLE_RUN_ID", "dotenv-marker")
        os.environ.setdefault("RESPAN_API_KEY", "test-key")

    monkeypatch.setattr(_shared, "load_dotenv", fake_load)
    _shared.load_root_env()
    assert _shared.marker() == "shell-marker"


def test_metadata_uses_exact_marker(monkeypatch):
    captured: dict[str, object] = {}

    class FakeRespan:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(_shared, "load_root_env", lambda: None)
    monkeypatch.setattr(_shared, "Respan", FakeRespan)
    monkeypatch.setenv("RESPAN_API_KEY", "test-key")
    _shared.make_respan("contract", "exact-marker")
    assert captured["metadata"]["example_run_id"] == "exact-marker"
    assert captured["metadata"]["run_id"] == "exact-marker"


def test_deterministic_logger_ignores_live_credentials(monkeypatch):
    monkeypatch.setattr(_shared, "load_root_env", lambda: None)
    monkeypatch.setenv("HELICONE_API_KEY", "must-not-be-used")
    monkeypatch.setattr(_shared, "endpoint", lambda: "http://127.0.0.1:9")
    logger = _shared.make_logger(live=False)
    assert logger.api_key == "local-helicone-example-key"
    assert logger.logging_endpoint == "http://127.0.0.1:9"


def test_runner_continues_and_aggregates(monkeypatch):
    calls: list[str] = []

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
    assert calls == ["first.py", "timeout.py", "last.py"]
    assert "first.py: exited 1" in str(caught.value)
    assert "timeout.py: timed out" in str(caught.value)


def test_runner_has_complete_feature_set():
    assert len(run_all.SCRIPTS) == 17
    for script in run_all.SCRIPTS:
        assert (EXAMPLE_DIR / script).is_file()
    assert (EXAMPLE_DIR / run_all.LIVE_SCRIPT).is_file()


def test_examples_do_not_print_or_embed_credentials():
    for filename in (
        *run_all.SCRIPTS,
        run_all.LIVE_SCRIPT,
        "_shared.py",
        "_local_sink.py",
    ):
        source = (EXAMPLE_DIR / filename).read_text(encoding="utf-8")
        assert "print(os.environ" not in source
        assert "sk-ant-" not in source
        assert "sk-proj-" not in source


def test_delayed_builder_is_not_a_workflow_result():
    source = (EXAMPLE_DIR / "13_delayed_builder_context.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    run_function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "run"
    )
    returns = [node for node in ast.walk(run_function) if isinstance(node, ast.Return)]
    assert len(returns) == 1
    assert isinstance(returns[0].value, ast.Constant)
    assert returns[0].value.value == "builder-created"
    assert "local-helicone-example-key" not in source
