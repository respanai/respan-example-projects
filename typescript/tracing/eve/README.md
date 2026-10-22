# Eve TypeScript tracing examples

Run real Eve agents, sessions, native streams, authored tools, and delegated
subagents with `@respan/instrumentation-eve`. Every model response comes from the
released `eve/evals` deterministic `mockModel`; no model-provider key is needed.
The suite exports controlled synthetic traces to the configured Respan account.

The current profile uses Eve 0.75.1 / AI SDK 7.0.136. The exact minimum profile
uses Eve 0.26.0 / AI SDK 7.0.26. `scripts/prepare.ts` selects the released API
shape and builds a disposable `.respan-eve/app` from the checked-in fixtures.
Current Eve owns the native OTel provider through `otel()` / `otelIntegration()`;
older Eve uses `RespanTelemetry` and `EveInstrumentor`. Both keep the export-time
privacy wrapper around their actual destination exporter.

## Install and run

Use Node.js 24 or newer. Set `RESPAN_API_KEY` in `respan-example-projects/.env`;
`RESPAN_BASE_URL` is optional.

Build the local instrumentation in the sibling `respan` checkout first:

```bash
cd ../respan/javascript-sdks
yarn workspace @respan/instrumentation-eve build
```

Then, from this example directory:

```bash
npm install --install-links
npm run typecheck
RESPAN_EXAMPLE_RUN_ID=eve-native-local npm run examples
```

`--install-links` packages the local target instrumentation instead of creating
a source symlink whose runtime imports could resolve to a different workspace
tracing package. SDK, tracing, and OTel companions resolve from their released
npm packages. For a separate worktree, install the built target tarball explicitly
with `npm install --save=false /absolute/path/to/respan-instrumentation-eve.tgz`.

To check the exact supported Eve/AI minimum with the same example sources:

```bash
npm install --install-links --save=false eve@0.26.0 ai@7.0.26 \
  @respan/respan-sdk@1.2.0 @respan/tracing@1.6.0
RESPAN_EXAMPLE_RUN_ID=eve-native-minimum npm run examples
```

The runner binds `127.0.0.1:23821`, waits for the actual health route, invokes the
released client APIs, consumes the native streams, waits for the batch exporter,
and closes the server. Set `EVE_EXAMPLE_PORT` to use another local port. Current
Eve uses a documented pure-JavaScript `JustBashSandbox` with automatic package
installation disabled and a synthetic anonymous channel bound by the local runner.
File memory uses Eve's built-in `fileMemory({ backend: inMemory() })`.

## Scenarios

The nine shared scenarios cover basic generation, structured weather tools,
delegated subagent lineage, false/zero/empty-string tool results, a real tool
exception, session continuation, and an 80,022-character native streamed response.
Current Eve adds two scenarios for native file-memory save and recall.

The suite prints its run ID and actual root/child session IDs. Query Respan using
`eve_typescript_<run-id>` as the workflow name, then inspect the actual trace
IDs, parent links, log types, full input/output, model/provider, and usage fields.
A continuation has two native turns; current Eve's delegated child is a native
child of its dispatch tool, while the minimum profile uses the helper's exact
session/turn lineage correlation.

Set `RESPAN_SPAN_NAME_STYLE=legacy` to retain original native names. Content
capture can be disabled with `RESPAN_TRACE_CONTENT=false` or
`TRACELOOP_TRACE_CONTENT=false`; assertions still verify native execution.
The constructor/context/sampling/privacy edge cases are covered in the paired
instrumentation package's native tests.

Eve 0.75.1 limits several telemetry attributes to 32 KiB. The large scenario
asserts that the actual SDK stream retains its complete response; it does not
claim that the SDK's emitted span restores data already truncated upstream.
Eve 0.26 emits the full corresponding telemetry payload.
