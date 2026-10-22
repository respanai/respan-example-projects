import { logExampleResult, runADKExample } from "./_shared.js";
const mode = process.argv[2] === "error" ? "error" : "privacy";
const workflowName = `Google ADK TS ${mode}.workflow`;
const result = await runADKExample({
  appName: "google-adk-typescript-examples",
  workflowName,
  mode,
  prompt: "Private controlled example prompt.",
});
logExampleResult(workflowName, {
  eventCount: result.events.length,
  errorCode: result.events.find((event) => event.errorCode)?.errorCode,
});
