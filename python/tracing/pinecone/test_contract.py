from __future__ import annotations

import ast
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import _shared
import pytest
import run_all

EXAMPLE_DIR = Path(__file__).resolve().parent


def _workflow_signature(filename: str) -> list[str]:
    module = ast.parse((EXAMPLE_DIR / filename).read_text())
    workflows = [
        node
        for node in ast.walk(module)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func.id == "workflow"
            for decorator in node.decorator_list
        )
    ]
    assert len(workflows) == 1
    return [argument.arg for argument in workflows[0].args.args]


def test_workflow_roots_accept_only_semantic_inputs():
    assert _workflow_signature("01_upsert_and_query.py") == ["topic", "top_k"]
    assert _workflow_signature("02_async_fetch.py") == ["vector_ids", "namespace"]
    assert _workflow_signature("03_expected_error.py") == ["namespace"]


def test_shell_marker_survives_dotenv(monkeypatch):
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "exact-shell-marker")

    def fake_load_dotenv(_path, *, override):
        assert override is False
        os.environ.setdefault("RESPAN_EXAMPLE_RUN_ID", "dotenv-marker")
        os.environ.setdefault("RESPAN_API_KEY", "test-key")

    monkeypatch.setattr(_shared, "load_dotenv", fake_load_dotenv)
    _shared.load_example_env()
    assert _shared.marker() == "exact-shell-marker"


def test_respan_and_workflow_metadata_use_exact_marker(monkeypatch):
    captured: dict[str, object] = {}

    class FakeRespan:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(_shared, "load_example_env", lambda: None)
    monkeypatch.setattr(_shared, "Respan", FakeRespan)
    monkeypatch.setenv("RESPAN_API_KEY", "test-key")
    _shared.create_respan("pinecone_contract", "exact-marker")

    assert captured["metadata"] == {
        "example_set": "pinecone",
        "workflow_name": "pinecone_contract",
        "example_run_id": "exact-marker",
        "run_id": "exact-marker",
    }
    attrs = _shared.workflow_attributes(
        "pinecone_contract", "exact-marker", "execution-1"
    )
    assert attrs["metadata"]["example_run_id"] == "exact-marker"
    assert attrs["metadata"]["run_id"] == "exact-marker"
    assert attrs["metadata"]["execution_id"] == "execution-1"


def test_runner_continues_and_aggregates_failures(monkeypatch):
    scripts = ("first.py", "timeout.py", "last.py")
    calls: list[str] = []

    def fake_run(command, **kwargs):
        script = Path(command[-1]).name
        calls.append(script)
        assert kwargs["env"]["RESPAN_EXAMPLE_RUN_ID"] == "runner-marker"
        if script == "timeout.py":
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        return SimpleNamespace(returncode=1 if script == "first.py" else 0)

    monkeypatch.setattr(run_all, "SCRIPTS", scripts)
    monkeypatch.setattr(run_all.subprocess, "run", fake_run)
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "runner-marker")
    with pytest.raises(SystemExit) as caught:
        run_all.main()
    assert calls == list(scripts)
    assert "first.py: exited 1" in str(caught.value)
    assert "timeout.py: timed out" in str(caught.value)


def test_runner_contains_complete_committed_set():
    assert run_all.SCRIPTS == (
        "01_upsert_and_query.py",
        "02_async_fetch.py",
        "03_expected_error.py",
        "04_documents.py",
        "05_async_listings.py",
    )
    for script in run_all.SCRIPTS:
        assert (EXAMPLE_DIR / script).is_file()


def test_print_result_is_json_native(capsys):
    _shared.print_result("contract", {"vector": [0.1, 0.2]}, "exact-marker")
    output = capsys.readouterr().out
    payload = output.split("== contract ==\n", 1)[1]
    assert json.loads(payload) == {"vector": [0.1, 0.2]}
