import { logExampleResult, runCohereWorkflow } from "./_shared.js";

const workflowName = "cohere_ts_rerank";

const result = await runCohereWorkflow(
  workflowName,
  async ({ client, clientV2 }) => {
    const documents = [
      "Respan captures traces for LLM applications.",
      "Bananas are yellow.",
    ];
    const v2 = await clientV2.rerank({
      model: "rerank-v4.0",
      query: "What observes LLM traces?",
      documents,
      topN: 1,
    });
    const v1 = await client.rerank({
      model: "rerank-v4.0",
      query: "What observes LLM traces?",
      documents,
      topN: 1,
    });
    return { v2, v1 };
  },
);

logExampleResult(workflowName, {
  v2TopIndex: result.v2.results?.[0]?.index,
  v1TopIndex: result.v1.results?.[0]?.index,
});
