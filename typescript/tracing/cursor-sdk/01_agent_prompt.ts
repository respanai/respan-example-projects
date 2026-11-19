import assert from "node:assert/strict";
import { scenario } from "./_shared.js";
await scenario("prompt", async (sdk, fixture) => {
  const result = await sdk.Agent.prompt("fixture prompt", fixture.options);
  assert.equal(result.status, "finished");
  assert.equal(result.result, "native Cursor answer");
  return { status: result.status, runId: result.id, usage: result.usage };
});
