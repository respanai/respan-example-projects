"""Actual released Marqo clients; deterministic native HTTP by default."""

import json

from _shared import marqo_client, run_case


def action(provider, local):
    from marqo.errors import MarqoWebError

    with marqo_client() as (client, _requests):
        try:
            client.index("docs").health()
        except MarqoWebError as error:
            assert error.status_code == 503
        else:
            raise AssertionError("native error expected")
    span = local.get_finished_spans()[-1]
    assert (
        span.status.status_code.name == "ERROR"
        and "traceloop.entity.output" not in span.attributes
    )
    assert "PRIVATE" not in json.dumps(dict(span.attributes))
    return "native503/error identity and diagnostics, no fabricated output"


if __name__ == "__main__":
    run_case("marqo_native_error", action)
