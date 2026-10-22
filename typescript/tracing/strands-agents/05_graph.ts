import {
  createGraph,
  logExampleResult,
  multiAgentText,
  runStrandsExample,
} from "./_shared.js";

const workflowName = "Strands Agents TS Graph.workflow";
const result = await runStrandsExample({
  appName: "strands-agents-typescript-examples",
  workflowName,
  fn: async () =>
    await createGraph().invoke("Build a compact Kyoto city brief."),
});

logExampleResult(workflowName, {
  output: multiAgentText(result),
  status: result.status,
  nodeCount: result.results.length,
});
