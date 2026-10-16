import assert from "node:assert/strict";
import { createAgent, logExampleResult, runStrandsExample } from "./_shared.js";
const workflowName = "Strands Agents TS Provider Error.workflow";
let failure: unknown;
try {
  await runStrandsExample({
    appName: "strands-agents-typescript-examples",
    workflowName,
    fn: async () =>
      await createAgent("error").invoke(
        "Exercise a controlled provider failure.",
      ),
  });
} catch (error) {
  failure = error;
}
assert.ok(failure instanceof Error);
logExampleResult(workflowName, { errorName: failure.name });
