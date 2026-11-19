import assert from "node:assert/strict";
import { scenario } from "./_shared.js";
await scenario("controlled-error", async (sdk, fixture) => {
  const agent = await sdk.Agent.create(fixture.options);
  const run = await agent.send("error");
  const result = await run.wait();
  assert.equal(result.status, "error");
  await agent[Symbol.asyncDispose]();
  return { status: result.status };
});
