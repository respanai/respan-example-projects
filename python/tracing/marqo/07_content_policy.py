"""Actual released Marqo clients; deterministic native HTTP by default."""

from _shared import marqo_client, run_case


def action(provider, local):
    from opentelemetry import context
    from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY

    with marqo_client() as (client, _requests):
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        try:
            assert len(client.index("docs").search(q="PRIVATE")["hits"]) == 75
        finally:
            context.detach(token)
        with provider.get_tracer("app").start_as_current_span(
            "private_parent", attributes={ENABLE_CONTENT_TRACING_KEY: False}
        ) as parent:
            parent.set_attribute(ENABLE_CONTENT_TRACING_KEY, True)
            client.index("docs").search(q="PRIVATE")
    owned = [s for s in local.get_finished_spans() if s.name.startswith("marqo.index")]
    assert len(owned) == 2 and all(
        "traceloop.entity.input" not in s.attributes
        and "traceloop.entity.output" not in s.attributes
        and not s.events
        and s.status.description is None
        for s in owned
    )
    return "unchanged SDKresults, canonical/ancestor denial, no private content"


if __name__ == "__main__":
    run_case("marqo_privacy", action)
