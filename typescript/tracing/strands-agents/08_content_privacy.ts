import { createAgent, logExampleResult, runStrandsExample } from "./_shared.js";
process.env.RESPAN_TRACE_CONTENT = "false";
const workflowName = "Strands Agents TS Privacy.workflow";
const result = await runStrandsExample({
  appName: "strands-agents-typescript-examples",
  workflowName,
  fn: async () => await createAgent("basic").invoke("private-example-prompt"),
});
logExampleResult(workflowName, { stopReason: result.stopReason });
