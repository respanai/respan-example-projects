from urllib.parse import urlsplit

from _shared import run_scenario, server
from elastic_transport import NodeConfig, Transport


def scenario():
    payload = {
        "properties": {
            "api_key": {"type": "string", "default": "controlled-schema-secret"}
        },
        "quoted": 'Bearer "controlled bearer secret"',
        "url": "https://example.invalid/path?api%5Fkey=controlled-url-secret",
        "zero": 0,
        "false": False,
        "empty": "",
    }
    with server(payload) as (url, requests):
        parsed = urlsplit(url)
        native = Transport([NodeConfig("http", parsed.hostname, parsed.port)])
        try:
            response = native.perform_request(
                "POST",
                "/controlled?api_key=controlled-query-secret",
                body={
                    "password": "controlled-request-secret",
                    "properties": payload["properties"],
                },
                headers={
                    "content-type": "application/json",
                    "authorization": "Bearer controlled-auth-secret",
                },
                max_retries=0,
                request_timeout=2.0,
            )
        finally:
            native.close()
        assert response.body == payload and len(requests) == 1
        return {
            "native_response_type": type(response).__name__,
            "native_requests": len(requests),
            "schema_properties_preserved": True,
        }


if __name__ == "__main__":
    run_scenario("08_transport_and_redaction", scenario)
