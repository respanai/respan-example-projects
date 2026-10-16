import pytest


@pytest.mark.parametrize("value", [0, False, 42, "native"])
def test_native_worker(value):
    assert value in (0, False, 42, "native")
