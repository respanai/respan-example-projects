import pytest


@pytest.fixture
def setup_failure():
    raise RuntimeError("controlled setup failure")


@pytest.fixture
def teardown_failure():
    yield 42
    raise RuntimeError("controlled teardown failure")


def test_setup(setup_failure):
    pass


def test_teardown(teardown_failure):
    assert teardown_failure == 42


@pytest.mark.xfail(strict=True, reason="controlled strict XPASS")
def test_strict_xpass():
    pass
