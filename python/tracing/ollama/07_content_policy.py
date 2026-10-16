from _shared import CHAT, MODEL, client, run_case
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def action(provider):
    c, body, _ = client(frames=[CHAT, CHAT])
    try:
        stream = c.chat(
            model=MODEL,
            messages=[{"role": "user", "content": "Controlled late private prompt"}],
            stream=True,
        )
        next(stream)
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        context.detach(token)
        list(stream)
        assert body.closed
    finally:
        c._client.close()
    c, _, _ = client()
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    try:
        assert c.chat(
            model=MODEL,
            messages=[{"role": "user", "content": "Controlled private prompt"}],
        ).message.content
    finally:
        context.detach(token)
        c._client.close()
    return "native results retained under initial and restored late content veto"


if __name__ == "__main__":
    run_case("ollama_content_policy", action)
