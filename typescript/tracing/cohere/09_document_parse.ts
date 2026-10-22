import { logExampleResult, runCohereWorkflow } from "./_shared.js";
const workflowName = "cohere_ts_document_parse";
const response = await runCohereWorkflow(workflowName, ({ clientV2 }) =>
  clientV2.parse({
    model: "parse-v5.0",
    document: {
      type: "image_url",
      imageUrl: "https://example.invalid/document.png",
    },
    outputFormat: "markdown",
  }),
);
logExampleResult(workflowName, { pages: response.pages.length });
