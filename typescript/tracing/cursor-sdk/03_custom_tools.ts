import assert from "node:assert/strict";
import { scenario } from "./_shared.js";
import { nativeLocalFixture } from "./_native_fixture.mjs";
await scenario("custom-tools", async (sdk) => {
  let observed: any;
  const customTools = {
    lookup_fixture: {
      description: "Return controlled values",
      inputSchema: { type: "object" },
      outputSchema: { type: "object" },
      annotations: { readOnlyHint: true },
      execute(args: any, context: any) {
        observed = { args, context };
        return { value: 0, empty: "", enabled: false };
      },
    },
  };
  const local = await nativeLocalFixture(sdk, customTools);
  if (!local)
    return {
      available: false,
      reason:
        "Native local fixture requires current public JsonlLocalAgentStore; older SDK cloud cases run separately.",
    };
  try {
    const agent = await sdk.Agent.create(local.options);
    const run = await agent.send("fixture");
    const result = await run.wait();
    await agent[Symbol.asyncDispose]();
    assert.equal(observed.context.toolCallId, "native-local-call");
    assert.equal(observed.context.sessionId, "native-child-session");
    assert.equal(result.usage?.totalTokens, 0);
    return {
      status: result.status,
      runId: run.id,
      usage: result.usage,
      toolContext: observed.context,
    };
  } finally {
    await local.close();
  }
});
