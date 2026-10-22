# Portkey tracing examples

These examples use the actual released Portkey SDK against controlled
HTTP/JSON/SSE transport responses. The default suite needs no credentials,
performs no live provider calls, and collects traces in memory.

```bash
python -m pip install -r requirements.txt
RESPAN_EXAMPLE_RUN_ID=portkey-check python run_all.py
```

The runner executes thirteen scripts with one marker, continues through failures
and timeouts, and reports any failure. Twelve scenarios are controlled; the
optional live scenario skips unless explicitly enabled. Coverage includes sync
and async chat, raw streams and native stream managers, current versus historical
tool calls and a connected tool result, 65 tool definitions with 120 properties each,
3,072-dimensional embeddings, Responses values/streams, structured parsing,
saved prompt/text calls, content opt-out, native 401 and stream transport errors.
The transport replaces no public SDK method.

Trace export is separate from model access:

```bash
RESPAN_PORTKEY_EXPORT=1 RESPAN_EXAMPLE_RUN_ID=portkey-export python run_all.py
```

Explicit export requires `RESPAN_API_KEY` in the environment or repository `.env`.
Optional `RESPAN_BASE_URL` defaults to `https://api.respan.ai/api`. Dotenv loading
uses `override=False`, so the exact shell marker and configuration are preserved.
Clients close and Respan flushes/shuts down in `finally` blocks.

To make the optional live call, set `RESPAN_PORTKEY_LIVE=1`, `PORTKEY_API_KEY`, and
your `PORTKEY_PROVIDER` or `PORTKEY_CONFIG`/model as appropriate. Optional
`PORTKEY_BASE_URL` overrides the gateway. Live calls can consume provider credits;
they are not part of the controlled validation. SDK framework integrations,
websocket/realtime/admin/raw-response APIs, remote prompt/account behavior and
production retry/fallback routing are not exercised by the fixtures.

The package supports Portkey 2.3.1–2.x and upstream instrumentor 0.1.11–0.1.x;
current and minimum fixture runs are recorded separately. Portkey bundles its own
OpenAI client, which is retained. For local adapter development, install the
released example requirements and then link only the target package explicitly.
