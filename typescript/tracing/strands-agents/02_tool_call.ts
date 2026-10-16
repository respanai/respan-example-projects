import {
  createAgent,
  logExampleResult,
  resultText,
  runStrandsExample,
} from "./_shared.js";

const workflowName = "Strands Agents TS Tool Call.workflow";
const result = await runStrandsExample({
  appName: "strands-agents-typescript-examples",
  workflowName,
  fn: async () =>
    await createAgent("tool").invoke("Use the weather tool for Tokyo."),
});

logExampleResult(workflowName, {
  output: resultText(result),
  stopReason: result.stopReason,
});
