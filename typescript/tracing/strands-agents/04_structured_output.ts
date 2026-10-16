import {
  cityBriefSchema,
  createAgent,
  logExampleResult,
  runStrandsExample,
} from "./_shared.js";

const workflowName = "Strands Agents TS Structured Output.workflow";
const result = await runStrandsExample({
  appName: "strands-agents-typescript-examples",
  workflowName,
  fn: async () =>
    await createAgent("structured", {
      structuredOutputSchema: cityBriefSchema,
    }).invoke("Return a structured city brief for Tokyo."),
});

logExampleResult(workflowName, {
  structuredOutput: result.structuredOutput,
  stopReason: result.stopReason,
});
