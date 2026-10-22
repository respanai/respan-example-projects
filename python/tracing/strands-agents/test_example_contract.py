from __future__ import annotations

import ast
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


def _is_workflow_decorator(node: ast.expr) -> bool:
    target = node.func if isinstance(node, ast.Call) else node
    return isinstance(target, ast.Name) and target.id == "workflow"


def test_shell_marker_wins_over_dotenv(monkeypatch):
    shared = _load("strands_example_shared_contract", EXAMPLE_DIR / "_shared.py")
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "shell-marker")
    monkeypatch.setenv("RESPAN_API_KEY", "test-key")
    monkeypatch.setattr(
        shared,
        "load_dotenv",
        lambda *_args, **_kwargs: os.environ.__setitem__(
            "RESPAN_EXAMPLE_RUN_ID", "dotenv-marker"
        ),
    )
    shared.load_example_environment()
    assert shared.new_run_id("case") == "shell-marker"


def test_all_examples_have_semantic_workflow_inputs_and_final_shutdown():
    assert len(SCRIPTS) == 11
    for script in SCRIPTS:
        source = script.read_text()
        tree = ast.parse(source)
        workflows = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and any(_is_workflow_decorator(item) for item in node.decorator_list)
        ]
        assert workflows, script.name
        assert all(node.args.args for node in workflows), script.name
        assert "finally:" in source
        assert "finish_respan(respan)" in source


def test_runner_continues_and_reports_aggregate_failures(monkeypatch, capsys):
    runner = _load("strands_example_runner_contract", EXAMPLE_DIR / "run_all.py")
    runner.SCRIPTS = [Path("01_ok.py"), Path("02_bad.py"), Path("03_ok.py")]
    calls = []

    def run(command, **_kwargs):
        calls.append(command[-1])
        return SimpleNamespace(returncode=7 if command[-1].endswith("02_bad.py") else 0)

    monkeypatch.setattr(runner.subprocess, "run", run)
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "runner-marker")
    assert runner.main() == 1
    assert calls == ["01_ok.py", "02_bad.py", "03_ok.py"]
    output = capsys.readouterr().out
    assert "RESPAN_EXAMPLE_RUN_ID=runner-marker" in output
    assert "02_bad.py:7" in output


def test_requirements_are_registry_portable():
    requirements = (EXAMPLE_DIR / "requirements.txt").read_text()
    assert "-e " not in requirements
    assert "../../" not in requirements
    assert "respan-instrumentation-strands-agents>=0.1,<1" in requirements
