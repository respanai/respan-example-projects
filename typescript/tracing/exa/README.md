# Exa + Respan (TypeScript)

Feature-compatible examples for `@respan/instrumentation-exa` and the npm-stable `exa-js@2.19.0` SDK.

The default mode starts a deterministic loopback HTTP server and exercises the real Exa SDK request, response, SSE, Agent, Research, and tool-helper code paths without consuming Exa credits. Set `RESPAN_EXA_LIVE=1` to use `EXA_API_KEY` for the core, streaming, tool, and Agent scenarios. The legacy Research scenario remains loopback-only because Exa deprecates `/research/v1` in favor of `search({ type: "deep-reasoning" })`.

## Setup

```bash
cd typescript/tracing/exa
npm install
```

The repository-root `.env` must contain `RESPAN_API_KEY`. `RESPAN_BASE_URL` is optional. Live mode also requires `EXA_API_KEY`.

## Run

```bash
npm run all
```

The suite uses one `RESPAN_EXAMPLE_RUN_ID` for exact platform lookup and runs:

- core search, contents, and grounded answer
- search and answer SSE streaming
- the npm 2.19 provider-neutral `webSearch` tool
- Agent `createAndWait` and loopback legacy Research compatibility
- a controlled provider error span in loopback mode

`exa-js@2.19.0` does not expose a `getContents` tool helper; core `getContents()` is covered. The additive helper appears in the tagged 2.20 source but was not on npm's `latest` dist-tag when this suite was authored.

Acceptance requires inspecting the scoped Respan trace trees and individual spans, including inputs/outputs, citations in `respan.metadata`, bare `llm` naming when the answer API supplies no model, error status, stream completion, provider-neutral entity names, hierarchy, and duplicate absence. Local exit code or exporter logs alone are not acceptance.
