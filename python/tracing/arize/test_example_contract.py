"""Check fixture/example execution and configuration contracts."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).parent


def test_fixture_keeps_public_arize_methods_native():
    source = (ROOT / "_fixture.py").read_text()
    assert "pool_manager.request=self.rest" in source.replace(" ", "")
    assert "session.send=self.send" in source.replace(" ", "")
    assert "_make_offline_method" not in source
    assert "setattr(client_class" not in source


def test_marker_env_policy_and_finally_cleanup():
    source = (ROOT / "_shared.py").read_text()
    assert "override=False" in source
    assert 'os.getenv("RESPAN_EXAMPLE_RUN_ID")' in source
    assert "if exporting:" in source
    assert "respan.flush()" in source and "respan.shutdown()" in source
    assert "finally:" in source


def test_runner_has_all_nine_examples_and_failure_aggregation():
    spec = importlib.util.spec_from_file_location(
        "arize_example_runner", ROOT / "run_all.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert len(module.EXAMPLES) == 9
    source = (ROOT / "run_all.py").read_text()
    assert "timeout=90" in source.replace(" ", "")
    assert "failures.append" in source
    assert "return 1" in source


def test_portable_released_requirements():
    source = (ROOT / "requirements.txt").read_text()
    assert "arize>=8.35.0,<9" in source
    assert "respan-ai>=4.2.3,<5" in source
    assert "respan-instrumentation-arize" in source
    assert "-e" not in source
