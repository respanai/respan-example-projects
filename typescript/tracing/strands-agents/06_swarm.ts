import {
  createSwarm,
  logExampleResult,
  multiAgentText,
  runStrandsExample,
} from "./_shared.js";

const workflowName = "Strands Agents TS Swarm.workflow";
const result = await runStrandsExample({
  appName: "strands-agents-typescript-examples",
  workflowName,
  fn: async () =>
    await createSwarm().invoke("Research Lisbon and hand off to a writer."),
});

logExampleResult(workflowName, {
  output: multiAgentText(result),
  status: result.status,
  nodeCount: result.results.length,
});
