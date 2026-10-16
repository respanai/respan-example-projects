from pathlib import Path

ROOT = Path(__file__).parent


def test_complete_runner_preserves_marker_and_collects_failures():
    runner = (ROOT / "run_all.py").read_text()
    scripts = sorted(ROOT.glob("0[1-8]_*.py"))
    assert len(scripts) == 8 and all(p.name in runner for p in scripts)
    assert 'os.getenv("RESPAN_EXAMPLE_RUN_ID")' in runner
    assert "timeout=180" in runner and "check=False" in runner
    assert "subprocess.TimeoutExpired" in runner


def test_fixture_default_and_event_flush_precede_shutdown():
    shared = (ROOT / "_shared.py").read_text()
    assert "override=False" in shared
    assert "FixtureServer().llm()" in shared
    assert shared.index("crewai_event_bus.flush()") < shared.index(
        "context.respan.shutdown()"
    )
    assert '"run_id": run_id' in shared


def test_requirements_portable_and_fixture_transport_local():
    requirements = (ROOT / "requirements.txt").read_text()
    assert "file:" not in requirements and " -e " not in requirements
    fixture = (ROOT / "_fixtures.py").read_text()
    assert "httpx.MockTransport" in fixture and "https://fixture.invalid/v1" in fixture
