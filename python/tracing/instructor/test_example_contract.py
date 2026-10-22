"""Example onboarding, marker and privacy contracts."""

import ast
from pathlib import Path

ROOT = Path(__file__).parent


def test_complete_runner():
    tree = ast.parse((ROOT / "run_all.py").read_text())
    scripts = next(
        ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "SCRIPTS" for t in n.targets)
    )
    assert len(scripts) == 11
    assert all((ROOT / s).is_file() for s in scripts)


def test_explicit_environment_preserved():
    source = (ROOT / "_respan_instructor.py").read_text()
    assert "override=False" in source and "override=True" not in source
    assert "RESPAN_EXAMPLE_EXPORT" in source and "RESPAN_EXAMPLE_RUN_ID" in source


def test_workflow_inputs_exclude_clients():
    source = (ROOT / "_respan_instructor.py").read_text()
    assert "return await function(*args, **kwargs)" in source
    assert "return function(*args, **kwargs)" in source
    assert "return invoke()" in source


def test_current_features_and_minimum_limits_documented():
    text = (ROOT / "README.md").read_text()
    assert "1.17" in text and "1.3.7" in text and "version skips" in text
    assert "token-budget" in text and "Responses" in text
