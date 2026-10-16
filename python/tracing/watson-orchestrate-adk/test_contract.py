from __future__ import annotations

import ast
from pathlib import Path

from _shared import load_repo_env, marker_for
from run_all import SCRIPTS

EXAMPLE_DIR = Path(__file__).resolve().parent


def test_shell_marker_survives_dotenv(monkeypatch) -> None:
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "shell-exact-marker")
    load_repo_env()
    assert marker_for("contract") == "shell-exact-marker"


def test_runner_covers_all_examples() -> None:
    assert SCRIPTS == tuple(sorted(EXAMPLE_DIR.glob("[0-9][0-9]_*.py")))
    assert len(SCRIPTS) == 9


def test_workflow_roots_take_semantic_arguments() -> None:
    for script in SCRIPTS:
        tree = ast.parse(script.read_text())
        workflows = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and any(
                isinstance(decorator, ast.Call)
                and getattr(decorator.func, "id", None) == "workflow"
                for decorator in node.decorator_list
            )
        ]
        assert workflows
        for workflow in workflows:
            names = [argument.arg for argument in workflow.args.args]
            assert names
            assert all(
                blocked not in name.lower()
                for name in names
                for blocked in ("client", "key", "credential", "token")
            )


def test_project_dependencies_are_registry_only() -> None:
    pyproject = (EXAMPLE_DIR / "pyproject.toml").read_text()
    assert "-e " not in pyproject
    assert "../../../../" not in pyproject
