import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def test_actual_protocol_client_values_and_cleanup():
    spec = importlib.util.spec_from_file_location(
        "native_protocol", HERE / "_protocol.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with module.Protocol() as native, native.client() as client:
        result = client.collections.use("Docs").query.fetch_objects(include_vector=True)
        assert type(result).__name__ == "QueryReturn" and len(result.objects) == 3
        assert len(native.grpc_requests) == 1
