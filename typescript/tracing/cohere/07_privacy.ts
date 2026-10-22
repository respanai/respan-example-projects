import { logExampleResult, runCohereWorkflow } from "./_shared.js";
const workflowName = "cohere_ts_privacy";
const result = await runCohereWorkflow(
  workflowName,
  async ({ clientV2 }) => {
    const response = await clientV2.chat({
      model: "command-a-03-2025",
      messages: [
        {
          role: "user",
          content: "This payload must not appear in the model span.",
        },
      ],
    });
    // The workflow receives only a non-content result, independent of model capture.
    return { received: !!response.message };
  },
  { traceContent: false },
);
logExampleResult(workflowName, {
  received: result.received,
  traceContent: false,
});
