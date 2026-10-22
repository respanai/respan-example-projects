"""Validate the local HTTPX fixture through the actual installed Ollama client."""

from _shared import CHAT, MODEL, client


def test_fixture_is_native_typed_http_response_and_deferred_ndjson():
    import ollama

    c, _, requests = client()
    try:
        response = c.chat(model=MODEL, messages=[])
        assert (
            type(response) is ollama.ChatResponse
            and response.message.content == CHAT["message"]["content"]
        )
        assert requests[0].url.path == "/api/chat"
    finally:
        c._client.close()
    c, body, requests = client(frames=[CHAT])
    try:
        stream = c.chat(model=MODEL, messages=[], stream=True)
        assert not requests and not body.reads
        assert type(next(stream)) is ollama.ChatResponse
        stream.close()
        assert body.closed
    finally:
        c._client.close()
