import grpc
from _protocol import Protocol
from _shared import run_scenario
from weaviate.exceptions import UnexpectedStatusCodeError, WeaviateQueryError


def scenario():
    with Protocol() as native, native.client() as client:
        native.grpc_error = grpc.StatusCode.INVALID_ARGUMENT
        try:
            client.collections.use("Docs").query.fetch_objects()
        except WeaviateQueryError:
            pass
        else:
            raise AssertionError("native gRPC error required")
        try:
            client.collections.use("Missing").config.get()
        except UnexpectedStatusCodeError as error:
            assert error.status_code == 404
        else:
            raise AssertionError("native HTTP error required")
        return {"native_errors": 2}


if __name__ == "__main__":
    run_scenario("expected-error", scenario)
