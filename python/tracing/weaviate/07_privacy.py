from _protocol import Protocol
from _shared import run_scenario
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def scenario():
    with Protocol() as native, native.client() as client:
        col = client.collections.use("Docs")
        col.data.insert(
            {
                "text": 'Bearer "controlled secret"',
                "schema": {
                    "properties": {
                        "api_key": {"type": "string", "default": "controlled"}
                    }
                },
                "flag": False,
                "zero": 0,
            }
        )
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        try:
            result = col.query.fetch_objects()
        finally:
            context.detach(token)
        assert len(result.objects) == 3
        return {"private_native_rows": len(result.objects)}


if __name__ == "__main__":
    run_scenario("privacy", scenario)
