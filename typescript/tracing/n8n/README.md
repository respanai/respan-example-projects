# n8n + Respan native OpenTelemetry examples

This example set exercises `@respan/instrumentation-n8n` without replacing
n8n's OpenTelemetry provider.

It contains two complementary cases:

- `example:deterministic` starts a real OpenTelemetry `NodeSDK`, invokes the
  exact `LegacyOpenTelemetry` implementation installed by n8n `2.37.7`
  (`@n8n/agents` `0.22.2`, `@ai-sdk/otel` `1.0.87`), and asserts the canonical
  workflow → task → agent → LLM → tool tree plus current query/save-memory
  tasks. It proves structural-wrapper suppression, reparenting, canonical
  content/usage, and request-header secret removal without credentials or
  network.
- `example:n8n` loads n8n `2.37.7`'s real compiled `OtelService` and
  `ExecutionLevelTracer`, starts the exact native `NodeSDK` + OTLP/Protobuf
  exporter path, and emits workflow/node spans through n8n's own span emitter.
  By default a loopback collector decodes the wire payload and asserts its
  canonical names, attributes, resource scope, status, and hierarchy.

## Requirements

- Node.js 24 LTS (tested with `24.19.0`; Node 25 is not a validated n8n runtime)
- npm
- no credential or network access for the default loopback run
- optional configured OTLP endpoint and headers for a separately authorized
  platform audit

## Install and run

Keep the local Respan packages linked while validating:

```bash
cd typescript/tracing/n8n
npm install --install-links=false
npm run example:deterministic
RESPAN_EXAMPLE_RUN_ID=n8n-local npm run example:n8n
```

Run `npm run examples` to execute both cases.

The deterministic Agent fixture remains in-memory by default. To send the
same already-asserted span batch through OTLP/HTTP Protobuf as an explicit
wire or platform audit, set the same opt-in variables used by the real-service
fixture:

```bash
export N8N_SMOKE_OTLP_ENDPOINT="http://127.0.0.1:4318"
export N8N_SMOKE_OTLP_PATH="/v1/traces"
RESPAN_EXAMPLE_RUN_ID=n8n-agent-wire-local npm run example:deterministic
```

For an authorized Respan audit, use the endpoint/path/header values below.
The script tees the transformed spans to its in-memory semantic assertions and
the configured OTLP exporter, does not print headers, and prints the exact
`run_id`, workflow name, and trace ID for scoped follow-up. Merely setting no
endpoint never opens a socket or sends data.

The real-native-service run deliberately avoids n8n's database, UI, and task
runner. n8n's generic execution command does not initialize the native OTel
backend module. Calling the real OTel service and execution-level tracer
directly gives deterministic coverage of provider construction and the emitted
wire contract.

To send the same native spans to an explicitly configured OTLP endpoint:

```bash
export RESPAN_API_KEY="your-respan-api-key"
export N8N_SMOKE_OTLP_ENDPOINT="https://api.respan.ai/api"
export N8N_SMOKE_OTLP_PATH="/v2/traces"
export N8N_SMOKE_OTLP_HEADERS="Authorization=Bearer ${RESPAN_API_KEY}"
RESPAN_EXAMPLE_RUN_ID=n8n-platform-audit npm run example:n8n
```

The script does not print headers or the API key. External export is opt-in;
without `N8N_SMOKE_OTLP_ENDPOINT`, it binds only to `127.0.0.1` on an ephemeral
port.

## Expected platform evidence

Query by the exact workflow names and the run time. The real n8n emitter creates
success and failure trees shaped like:

```text
workflow
└── task   (Prepare deterministic output)

workflow  (failed)
└── task   (Fail deterministically, failed)
```

Inspect the full tree and individual spans, not only trace presence. Verify:

- the root metadata includes the n8n workflow ID/name/version, execution ID,
  mode, final status, and node count;
- the task includes its n8n node ID/name/type/version and item counts;
- task parent IDs point to the workflow span;
- raw `n8n.*` attributes and off-contract aliases are absent after canonical
  promotion;
- resource attributes retain n8n service version, instance ID, and instance
  role;
- successful spans retain OK/200 status, while the failure tree retains
  ERROR/500 status and exception events on both workflow and task.

For an opt-in deterministic Agent export, query by its printed workflow name
(`n8n deterministic native spans <run_id>`) and trace ID. Verify the seven-span
tree shown below, the LLM prompt/completion/tool/usage attributes, memory
metadata, wrapper-free hierarchy, and absence of raw `ai.*` fields or the fake
Authorization sentinel. This is the provider-free Agent wire/platform gate;
it does not require a model credential.

The deterministic case additionally covers the current n8n Agent tree:

```text
workflow
└── task                    (Run support agent)
    └── agent.support-agent
        ├── llm.gpt-4o-mini
        │   └── tool.lookup_customer
        ├── task            (query_memory)
        └── task            (save_memory)
```

The source emits an outer `ai.generateText` and an `ai.toolCall` in this tree;
semantic export removes only those structural duplicates and reparents their
canonical children. The assertions also verify indexed prompt/completion
content, model and token usage, tool arguments/results, memory metadata, and
absence of raw `ai.*` fields and a fake Authorization-header sentinel. A live
provider-backed Agent case should be added only with a stable n8n Agents
creation fixture and an authorized provider credential; the legacy LangChain
AI Agent node does not emit n8n's current `gen_ai.*` Agent spans.
