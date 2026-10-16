from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = tuple(sorted(ROOT.glob("[0-1][0-9]_*.py")))


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_exact_marker_and_runner_contract() -> None:
    shared = _source(ROOT / "_shared.py")
    runner = _source(ROOT / "run_all.py")
    assert "override=False" in shared
    assert 'os.getenv("RESPAN_EXAMPLE_RUN_ID", DEFAULT_RUN_ID)' in shared
    assert "env.setdefault" in runner
    assert "subprocess.TimeoutExpired" in runner
    assert "check=False" in runner
    assert all(path.name in runner for path in SCRIPTS)


def test_workflow_roots_use_semantic_inputs_and_shutdown() -> None:
    for path in SCRIPTS:
        tree = ast.parse(_source(path))
        workflows = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and any(
                isinstance(decorator, ast.Call)
                and getattr(decorator.func, "id", None) == "workflow"
                for decorator in node.decorator_list
            )
        ]
        assert len(workflows) == 1
        assert [argument.arg for argument in workflows[0].args.args]
        assert "respan.shutdown()" in _source(path)


def test_failure_and_stream_scenarios_are_contract_shaped() -> None:
    failure = _source(ROOT / "03_expected_tool_failure.py")
    stream = _source(ROOT / "04_streaming_agent.py")
    assert "except RuntimeError" in failure
    assert "list(agent.run" not in stream
    assert 'getattr(chunk, "output", None)' in stream


def test_requirements_are_registry_portable() -> None:
    requirements = _source(ROOT / "requirements.txt")
    assert " -e " not in requirements
    assert "file:" not in requirements


def test_fixture_mode_is_default_and_live_model_is_explicit() -> None:
    shared = _source(ROOT / "_shared.py")
    assert 'os.getenv("SMOLAGENTS_MODEL_MODE", "fixture")' in shared
    assert 'if mode != "live"' in shared
    assert len(SCRIPTS) == 10
