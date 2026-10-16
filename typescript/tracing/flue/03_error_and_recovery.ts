import assert from "node:assert/strict";
import { context } from "@opentelemetry/api";
import { CONTEXT_KEY_ALLOW_TRACE_CONTENT } from "@traceloop/ai-semantic-conventions";
import { runtime } from "./_native.mjs";
import { runNativeExample, shutdownNativeExamples } from "./_shared.js";

await runNativeExample(
  "Flue Native Provider Error",
  { providerError: true },
  async (native) => {
    await assert.rejects(native.prompt(), runtime.OperationFailedError);
  },
);
await runNativeExample(
  "Flue Native Tool Error and Recovery",
  { tool: true, toolError: new Error("controlled native tool rejection") },
  async (native) => {
    assert.equal((await native.prompt()).text, "native answer");
    assert.equal(native.calls.length, 1);
  },
);
await context.with(
  context.active().setValue(CONTEXT_KEY_ALLOW_TRACE_CONTENT, false),
  () =>
    runNativeExample(
      "Flue Native Content Veto",
      { tool: true },
      async (native) => {
        assert.equal((await native.prompt()).text, "native answer");
      },
    ),
);

await shutdownNativeExamples();
