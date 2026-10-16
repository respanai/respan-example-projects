# Flue TypeScript tracing examples

These examples run genuine released Flue agents/harnesses and Pi's OpenAI
transport against a controlled localhost provider. They require no production
model credentials. Runtime events are emitted by Flue itself.

The seven scenarios cover complete 80 KB prompt/response and tool-schema
content, a 5001-element vector tool result, `false`/`0`/empty values, real tool
calls, native call handles and cancellation signals, session continuation,
delegated tasks, explicit compaction, provider failure, tool failure/recovery,
and content privacy. Respan workflow helpers group the activity for inspection.

Build `@respan/instrumentation-flue` in the sibling Respan checkout before
installing these source examples. The `file:` dependency expects its compiled
`dist` directory. Core Respan companions resolve from released npm packages.
For an isolated worktree or packed consumer, use an explicit target override:

```bash
RESPAN_FLUE_PACKAGE_TARBALL=/absolute/path/respan-instrumentation-flue-0.1.0.tgz npm run setup:local
# Alternatively, after building that package:
RESPAN_SDK_ROOT=/absolute/path/respan npm run setup:local
```

Set `RESPAN_API_KEY` in the repository-root `.env`. `RESPAN_BASE_URL` and
`RESPAN_EXAMPLE_RUN_ID` are optional. Then run:

```bash
npm install
RESPAN_EXAMPLE_RUN_ID=flue-ts-native npm run examples
```

The default profile is `@flue/runtime@2.2.2` with
`@flue/opentelemetry@2.2.2`. The same scenarios support the declared minimum:

```bash
npm install @flue/runtime@1.0.0-beta.1 @flue/opentelemetry@1.0.0-beta.1 @earendil-works/pi-ai@0.79.4
RESPAN_EXAMPLE_RUN_ID=flue-ts-native-min npm run examples
```

Flue 2.2.2 uses agent functions/hooks and a harness conversation; the beta uses
created agents and named sessions. `_native.mjs` provides the appropriate genuine
SDK calls for each installed release. Its internal context construction is a
local host adapter for these examples; application agent code should use Flue's
public application setup. The localhost server supplies controlled OpenAI wire
responses, including exact native tool-call IDs and real provider usage fields.
No events, SDK classes, or model operations are fabricated by the examples.
