from pathlib import Path

from run_all import SCRIPTS


def test_runner_covers_all_controlled_and_live_cases():
    root = Path(__file__).parent
    assert SCRIPTS == tuple(sorted(root.glob("[0-9][0-9]_*.py")))
    assert len(SCRIPTS) == 8
    source = (root / "_fixtures.py").read_text()
    assert "PredictionServiceGrpcTransport" in source
    assert "Native client cache did not select loopback transport" in source
    assert "sys.modules" not in source and "object.__new__" not in source


def test_exports_and_live_calls_require_separate_optins():
    root = Path(__file__).parent
    assert (
        'os.getenv("RESPAN_EXAMPLE_EXPORT") == "1"' in (root / "_shared.py").read_text()
    )
    assert (
        'os.getenv("VERTEXAI_EXAMPLE_LIVE") != "1"'
        in (root / "06_live_provider.py").read_text()
    )
