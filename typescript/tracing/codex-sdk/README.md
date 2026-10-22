# Codex SDK tracing examples

Run the released `@openai/codex-sdk` 0.162.1 through Respan with controlled CLI
JSONL subprocess transports. The actual SDK owns `Codex`, `Thread`, option
serialization, JSONL parsing, results, and iteration. The default examples do
not execute the native Codex CLI or model inference, and require no provider
or Respan key. The executable transport fixture requires a Unix-like system
and Node.js 20.12 or newer on `PATH`.

Keep `respan` and `respan-example-projects` as sibling checkouts. Build the
Codex instrumentation first, then install this example directory:

```bash
npm ci
npm run typecheck
npm run examples
```

`.npmrc` installs the local target as a material copy. The facade, tracing
runtime, and contract packages resolve from released npm versions. Reinstall
after rebuilding the local target; an existing material copy does not update
when its source changes.

- `01_basic_turn.ts`: all eight native item variants, aggregate turn usage,
  MCP content/structured content/_meta, 82 nested argument records, and a
  5001-element MCP result vector.
- `02_streamed_turn.ts`: actual events and native iterator identity.
- `03_structured_output.ts`: native output-schema transport and JSON response.
- `04_image_input.ts`: 80 text parts plus an ordered local-image input part.
- `05_resume_thread.ts`: two native turns with the same thread identity.
- `06_workspace_file_change.ts`: native file-change event mapping. The
  controlled transport reports a fixture change; it does not modify a file.
- `07_expected_error.ts`: native turn, process, JSONL, and AbortSignal failures.
- `08_privacy_and_lifecycle.ts`: content opt-out, turn-only capture, in-flight
  deactivation, reactivation, and early iterator return.
- `09_current_sdk_options.ts`: current raw config overrides, thread source,
  turn cyber-program selection, and cache-write usage. This script reports a
  skip on the supported 0.141.0 SDK minimum rather than injecting newer fields
  into an older protocol.

Each script runs in a separate process. Set `RESPAN_EXAMPLE_CAPTURE_PATH` to
inspect the actual public-runtime span IDs, parent links, attributes, and
status. Give separate scripts separate capture paths.

To export the same controlled traces through the normal Respan pipeline:

```bash
RESPAN_EXAMPLE_EXPORT=1 RESPAN_API_KEY="$RESPAN_API_KEY" \
  RESPAN_EXAMPLE_RUN_ID="codex-sdk-audit" npm run examples
```

Use `RESPAN_BASE_URL` only to select your configured Respan trace destination.
The provider transport stays local in export mode. No Gateway compatibility
is implied by the native SDK's custom base-URL option.

For explicit live inference, set `CODEX_EXAMPLE_LIVE=1` and `CODEX_API_KEY` or
`OPENAI_API_KEY`; optionally set `CODEX_MODEL` and `CODEX_BASE_URL`. Live mode
uses the native Codex executable and may perform the requested workspace
operations. Controlled fixture assertions are disabled for live responses.

A native turn is an agent span, with actual tool/task item children. Aggregate
turn usage and the explicitly configured model are canonical JSON metadata.
The SDK does not expose individual provider requests, complete conversation
history, available tool definitions, or provider call IDs, so these examples
do not fabricate them. Generic item identities remain in `codex_item_id`
metadata; `gen_ai.tool.call.id` is omitted because no invocation/call ID is exposed.
The array of nested MCP argument records is test payload, not an available
model-tool schema list.

The privacy script also uses `RESPAN_TRACE_CONTENT=false` for its explicit
workflow decorator. The released runtime's workflow decorator is separate
from the instrumentor's constructor/context privacy gates.
