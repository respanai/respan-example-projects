import { logExampleResult, runCohereWorkflow } from "./_shared.js";

const workflowName = "cohere_ts_embeddings";

const result = await runCohereWorkflow(
  workflowName,
  async ({ client, clientV2 }) => {
    const v2 = await clientV2.embed({
      model: "embed-v4.0",
      texts: ["Respan traces AI applications."],
      inputType: "classification",
      embeddingTypes: ["float", "int8", "uint8", "binary", "ubinary"],
    });
    const v1 = await client.embed({
      model: "embed-v4.0",
      texts: ["Cohere embeddings example."],
      inputType: "classification",
      embeddingTypes: ["float", "int8", "uint8", "binary", "ubinary"],
    });
    return { v2, v1 };
  },
);

logExampleResult(workflowName, {
  v2Types: Object.keys(result.v2.embeddings ?? {}),
  v1ResponseType: result.v1.responseType,
});
