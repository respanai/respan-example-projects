import {
  createAgent,
  logExampleResult,
  resultText,
  runStrandsExample,
} from "./_shared.js";

const workflowName = "Strands Agents TS Basic Invoke.workflow";
const result = await runStrandsExample({
  appName: "strands-agents-typescript-examples",
  workflowName,
  fn: async () =>
    await createAgent("basic").invoke(
      "Say hello from Strands Agents TypeScript.",
    ),
});

logExampleResult(workflowName, {
  output: resultText(result),
  stopReason: result.stopReason,
});
