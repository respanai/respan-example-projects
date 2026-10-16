import assert from "node:assert/strict";
import { runExample, MODEL } from "./_shared.js";
await runExample("fallback", async ({ client, fixture }) => {
  if (fixture) fixture.plan.fallback = true;
  const result = await client.guard({
    input: "controlled fallback",
    model: MODEL,
    fallbackModel: "openai/gpt-4o-mini",
    chunkSize: 0,
  });
  if (fixture) assert.equal(fixture.requests.length, 2);
  return result;
});
