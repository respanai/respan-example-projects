import assert from "node:assert/strict";
import { createAgent, logExampleResult, runStrandsExample } from "./_shared.js";
const workflowName = "Strands Agents TS Large Payload.workflow";
const result = await runStrandsExample({
  appName: "strands-agents-typescript-examples",
  workflowName,
  fn: async () =>
    await createAgent("large").invoke(
      Array.from({ length: 75 }, (_, i) => ({
        role: i % 2 ? ("assistant" as const) : ("user" as const),
        content: [{ text: `history-${i}` }],
      })),
    ),
});
const output = JSON.parse(result.toString());
assert.equal(output.vector.length, 5001);
assert.equal(output.zero, 0);
assert.equal(output.falsy, false);
assert.equal(output.empty, "");
assert.equal(output.nothing, null);
logExampleResult(workflowName, {
  vectorLength: output.vector.length,
  historyLength: 75,
});
