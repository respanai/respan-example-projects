import assert from "node:assert/strict";
import { scenario } from "./_shared.js";
await scenario(
  "content-opt-out",
  async (sdk, fixture) => {
    const agent = await sdk.Agent.create(fixture.options);
    const run = await agent.send("private fixture prompt");
    assert.equal((await run.wait()).status, "finished");
    await agent[Symbol.asyncDispose]();
    return { status: "finished" };
  },
  false,
);
