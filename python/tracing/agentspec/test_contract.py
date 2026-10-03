"""Execution-boundary checks for the standalone example suite."""

import ast
from pathlib import Path

ROOT = Path(__file__).parent


def test_all_default_scenarios_close_respan_and_use_fixture_factories():
    scripts = sorted(ROOT.glob("[0-9][0-9]_*.py"))
    assert len(scripts) == 9
    for script in scripts:
        source = script.read_text()
        tree = ast.parse(source)
        assert any(
            isinstance(node, ast.Try)
            and any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "shutdown"
                for item in node.finalbody
                for child in ast.walk(item)
            )
            for node in ast.walk(tree)
        ), script.name
        if script.name != "06_tool_flow.py":
            assert "fixture_model" in source, script.name
        assert "configure_gateway" not in source and "OPENAI_API_KEY" not in source


def test_markers_and_external_environment_are_preserved():
    shared = (ROOT / "_shared.py").read_text()
    runner = (ROOT / "run_all.py").read_text()
    assert "override=False" in shared
    assert "RESPAN_EXAMPLE_RUN_ID" in shared
    assert "setdefault" in runner and "RESPAN_EXAMPLE_RUN_ID" in runner
    assert "timeout=90" in runner and "check=False" in runner


def test_fixture_intercepts_model_construction_and_requirements_are_portable():
    fixture = (ROOT / "_fixtures.py").read_text()
    assert "_create_chat_openai_model" in fixture and "patch.object" in fixture
    requirements = (ROOT / "requirements.txt").read_text()
    assert "/Users/" not in requirements and "-e " not in requirements
    assert "pyagentspec[langgraph]>=26.3.1" in requirements
