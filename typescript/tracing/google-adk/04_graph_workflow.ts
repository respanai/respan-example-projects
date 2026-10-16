import { logExampleResult, runADKExample } from "./_shared.js";
const workflowName = "Google ADK TS Graph.workflow";
const result = await runADKExample({
  appName: "google-adk-typescript-examples",
  workflowName,
  mode: "graph",
  prompt: "Prepare the local forecast.",
});
logExampleResult(workflowName, {
  output: result.events.at(-1)?.output,
  eventCount: result.events.length,
});
