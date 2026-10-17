# Cursor SDK tracing examples

These examples exercise the released `@cursor/sdk` 1.0.37 through Respan. They use native SDK objects with deterministic transports and do not call Cursor cloud or run workspace commands.

Requires Node.js 22.13 or newer and a checkout with `respan` and `respan-example-projects` as siblings. The instrumentor is installed as a material copy (`install-links=true`); the Respan facade/runtime/contract packages resolve from npm.

```bash
npm ci
npm run all
```

- `01_agent_prompt.ts`: native one-shot prompt and aggregate usage.
- `02_agent_stream.ts`: multimodal input, model override, full 80-item tool arguments and 5001-element output, native stream/wait, detached `getRun()`, and resumed follow-up.
- `03_custom_tools.ts`: actual local SDK callback context, output schemas, annotations, and zero usage. Its deterministic executor replaces the public platform transport; the agent and run remain native. Older SDKs without the public JSONL store report this feature fixture as unavailable.
- `04_privacy_errors.ts`: native structured error.
- `05_content_opt_out.ts`: content opt-out on both the runtime and plugin.

Each script prints the run marker and native result summary. For local span inspection, set `RESPAN_EXAMPLE_CAPTURE_PATH` to a JSON output path. Run separate scripts with separate paths.

To export through the normal Respan pipeline, set `RESPAN_EXAMPLE_EXPORT=1`, `RESPAN_API_KEY`, and optionally `RESPAN_BASE_URL` in your process environment. Set `RESPAN_EXAMPLE_RUN_ID` to correlate the exact audit run. The Cursor provider transport remains the owned fixture.

Agent runs are agent spans; model selection and aggregate token usage are canonical metadata. Actual native tool events generate tool spans with their real invocation IDs. The examples do not manufacture provider LLM children or infer missing usage.
