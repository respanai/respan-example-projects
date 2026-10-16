from __future__ import annotations

import ast
import os
from pathlib import Path

import _shared
import run_all
from _shared import example_run_id


def test_shell_marker_wins_over_repository_env(monkeypatch):
    marker = "openinference-shell-marker"
    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", marker)
    assert example_run_id() == marker
    assert run_all.resolved_run_id() == marker


def test_run_all_lists_every_example_once():
    directory = Path(__file__).resolve().parent
    expected = tuple(
        path.name
        for path in sorted(directory.glob("[0-9][0-9]_*.py"))
        if path.name != "test_example_contract.py"
    )
    assert run_all.EXAMPLE_SCRIPTS == expected
    assert len(set(run_all.EXAMPLE_SCRIPTS)) == len(run_all.EXAMPLE_SCRIPTS)


def test_common_metadata_and_streaming_source_uses_upstream_openinference(monkeypatch):
    captured = {}
    from contextlib import contextmanager

    @contextmanager
    def capture(**kwargs):
        captured.update(kwargs)
        yield

    monkeypatch.setattr(_shared, "propagate_attributes", capture)
    with _shared.example_attributes("streaming-privacy", "contract-test-marker"):
        pass
    assert captured["metadata"]["run_id"] == "contract-test-marker"
    assert captured["metadata"]["example"] == "streaming-privacy"
    streaming_source = (Path(__file__).parent / "05_streaming_privacy.py").read_text()
    assert "OISpanAttributes.LLM_INVOCATION_PARAMETERS" in streaming_source
    assert '"stream": True' in streaming_source
    assert '"gen_ai.is_streaming"' not in streaming_source


def test_every_public_example_finishes_respan_in_finally():
    directory = Path(__file__).resolve().parent
    for script in run_all.EXAMPLE_SCRIPTS:
        tree = ast.parse((directory / script).read_text())
        finally_calls = [
            node
            for candidate in ast.walk(tree)
            if isinstance(candidate, ast.Try)
            for node in ast.walk(ast.Module(body=candidate.finalbody, type_ignores=[]))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "finish_respan"
        ]
        assert finally_calls, f"{script} must call finish_respan() from finally"


def test_run_all_aggregates_process_failures_and_timeouts(monkeypatch):
    outcomes = iter((0, 2, "timeout", 3, *([0] * (len(run_all.EXAMPLE_SCRIPTS) - 4))))
    calls = []

    class Result:
        def __init__(self, returncode):
            self.returncode = returncode

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        outcome = next(outcomes)
        if outcome == "timeout":
            raise run_all.subprocess.TimeoutExpired(args[0], kwargs["timeout"])
        return Result(outcome)

    monkeypatch.setenv("RESPAN_EXAMPLE_RUN_ID", "contract-test-marker")
    monkeypatch.setattr(run_all.subprocess, "run", fake_run)
    assert run_all.main() == 1
    assert len(calls) == len(run_all.EXAMPLE_SCRIPTS)
    assert all(
        kwargs["timeout"] == run_all.EXAMPLE_TIMEOUT_SECONDS for _, kwargs in calls
    )
    assert os.environ["RESPAN_EXAMPLE_RUN_ID"] == "contract-test-marker"
