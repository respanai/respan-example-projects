from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = tuple(sorted(ROOT.glob("0[1-9]_*.py")))


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


def test_workflow_roots_have_semantic_inputs_and_nested_teardown() -> None:
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
        source = _source(path)
        assert "await close_kernel_clients()" in source
        assert "respan.shutdown()" in source


def test_failure_escapes_decorated_workflow() -> None:
    source = _source(ROOT / "04_function_failure.py")
    tree = ast.parse(source)
    workflow = next(
        node
        for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "run_function_failure"
    )
    assert not any(isinstance(node, ast.Try) for node in ast.walk(workflow))
    assert "except (RuntimeError, KernelInvokeException)" in source


def test_requirements_are_registry_portable() -> None:
    requirements = _source(ROOT / "requirements.txt")
    assert " -e " not in requirements
    assert "file:" not in requirements
