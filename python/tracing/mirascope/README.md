# Mirascope tracing examples

Runs real Mirascope 2.5 Model/Toolkit response and stream objects with controlled
providers and mock HTTP. The complete runner defaults to fixtures; paid gateway
inference requires `RESPAN_MIRASCOPE_RUN_LIVE=1`.

```bash
cd python/tracing/mirascope
pip install -r requirements.txt
RESPAN_EXAMPLE_RUN_ID=mirascope-audit-YYYYMMDDTHHMMSSZ python run_all.py
```

For an unpublished adapter, install released companion packages from the
requirements, then link only `respan-instrumentation-mirascope` from the SDK
checkout. Do not replace Respan core with an editable copy when validating the
adapter's dependency floors.

The scripts load repository-root `.env` with `override=False`, preserve explicit
environment settings, flush and shut down Respan, and append the exact run marker
to trace-group identifiers and metadata. `RESPAN_API_KEY` and `RESPAN_BASE_URL`
configure trace export. Optional `RESPAN_GATEWAY_API_KEY`,
`RESPAN_GATEWAY_BASE_URL` and `RESPAN_MODEL` apply only to the live script.
The mock HTTP OpenAI/XAI clients use synthetic credentials and do not call a
provider service. Trace export still requires a valid Respan key.

| Script | Native coverage |
| --- | --- |
| `01_call_and_tool.py` | Model.call, current ToolCall and Toolkit.execute |
| `02_sync_async_stream.py` | Sync/async streams consumed through native text_stream |
| `03_expected_error.py` | Actual provider503 exception |
| `04_privacy.py` | Initial capture_content=False, metadata/actual usage retained |
| `05_live_gateway.py` | Optional gateway call; explicit skip by default |
| `06_context_calls_and_toolkits.py` | Four context Model methods and all four Toolkit variants |
| `07_controlled_provider_http.py` | Native OpenAI Completions, streaming, Responses and Mirascope2.5 XAI; absent/zero/invalid/cache/reasoning source counters |
| `08_complete_tools_and_history.py` | 150 messages, current/history IDs, single-encoded args, sensitive schema property, dense/sparse5000-value tool results |
| `09_stream_errors_and_veto.py` | Before-first-content and partial errors, native source early close, delayed stream after private parent detach |

The adapter owns the eight native Model methods and four Toolkit methods.
Provider methods or response operations that bypass them are not separate
instrumentation surfaces. Native response values and errors remain unchanged;
each raw stream advance attaches/detaches its span. Mirascope text_stream adds a
newline when text ends and closing its outer generator does not guarantee inner
source close; consume it or close `_chunk_iterator` when abandoning it.

Complete canonical entity input/output retains all messages and known tool/vector
payloads. Indexed prompt/completion projections are limited to eight each to
preserve common attributes under the default OTel budget. Only actual provider
usage is emitted: Mirascope default-zero fields without a raw source do not
establish zero usage. Local, wire and stored-trace checks are separate; backend
status, usage, streaming and tool projections may differ from exported spans.
Live gateway/provider inference is not covered by default fixture success.
