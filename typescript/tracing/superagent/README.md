# Superagent + Respan TypeScript examples

These examples use released `safety-agent` 0.1.7 and the local Superagent instrumentation package. Companion Respan packages come from npm. Node.js 24 is used for validation.

## Setup and run

Build the instrumentation in the sibling `respan` checkout first, then install the example as a normal npm consumer:

```bash
cd ../respan/javascript-sdks
yarn install --immutable
yarn workspace @respan/instrumentation-superagent build
cd ../../respan-example-projects/typescript/tracing/superagent
npm ci
npm run typecheck
npm run all
```

By default, native SDK calls use controlled provider HTTP responses and a controlled Daytona HTTP adapter. No model provider requests, sandbox creation, or trace exports leave the process. `ws` supplies the peer required by Daytona's native transport.

| Script                 | Native behavior                                                             |
| ---------------------- | --------------------------------------------------------------------------- |
| `01_guard.ts`          | Chunked guard calls, with one model span per native provider transformation |
| `02_redact.ts`         | Redaction, entities, and `rewrite: false`                                   |
| `03_workflow.ts`       | Guard and redact beneath Respan workflow/task parents                       |
| `04_scan.ts`           | Actual Daytona scan lifecycle, report parsing, and sandbox cleanup          |
| `05_fallback.ts`       | Version 0.1.7 fallback request after a controlled provider failure          |
| `06_privacy.ts`        | Canonical context content veto with unchanged native result                 |
| `07_provider_error.ts` | Original native error identity and failed spans                             |
| `08_large_payload.ts`  | Complete long input, 5001 values, and false/zero/empty/null                 |

Each script prints only its run marker and counts. Set `SUPERAGENT_CAPTURE_DIR` to save the controlled canonical spans locally.

## Export controlled traces

Place `RESPAN_API_KEY` in the repository root `.env` and enable export explicitly:

```bash
RESPAN_EXAMPLE_EXPORT=1 RESPAN_EXAMPLE_RUN_ID=my-superagent-run npm run all
```

`RESPAN_BASE_URL` optionally selects the trace endpoint. Provider calls remain controlled unless live mode is also enabled.

## Live provider calls

`SUPERAGENT_EXAMPLE_PROVIDER=live` enables real provider calls. Set `SUPERAGENT_API_KEY`, the provider's native key such as `OPENAI_API_KEY`, and `SUPERAGENT_MODEL` (for example `openai/gpt-4o-mini`). Run an individual applicable script. The controlled fallback, error, and payload assertions are fixture scenarios. A live scan additionally requires `DAYTONA_API_KEY` and `SUPERAGENT_SCAN_REPO`; it creates and deletes a remote sandbox.

Scan spans contain the native scan result. Remote model requests inside Daytona are not observable through this SDK, so the instrumentation does not invent child model spans. Failed attempts have no fabricated completion or HTTP status. The minimum supported 0.1.6 predates the explicit `fallbackModel` option.

The SDK may retry a timed-out HTTP request with a reused transformed body. Such transport retries do not expose another provider transformation, so this adapter cannot distinguish them as separate model spans. Explicit `fallbackModel` calls do expose distinct transformations and are covered.
