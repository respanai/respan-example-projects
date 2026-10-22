import assert from "node:assert/strict";
import {
  runExample,
  MODEL,
  context,
  CONTEXT_KEY_ALLOW_TRACE_CONTENT,
} from "./_shared.js";
const spans = await runExample("privacy", async ({ client }) =>
  context.with(
    context.active().setValue(CONTEXT_KEY_ALLOW_TRACE_CONTENT, false),
    () =>
      client.guard({
        input: "PRIVATE_SUPERAGENT_SENTINEL",
        model: MODEL,
        chunkSize: 0,
      }),
  ),
);
assert.ok(!JSON.stringify(spans).includes("PRIVATE_SUPERAGENT_SENTINEL"));
