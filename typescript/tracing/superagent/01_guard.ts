import assert from "node:assert/strict";
import { runExample, MODEL } from "./_shared.js";
await runExample("guard", async ({ client, fixture }) => {
  const result = await client.guard({
    input: "controlled input with several chunks",
    model: MODEL,
    chunkSize: 8,
  });
  assert.ok(result.classification);
  if (fixture) assert.ok(fixture.requests.length > 1);
  return result;
});
