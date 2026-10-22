import {
  createAzureClient,
  createRespan,
  logExampleResult,
  runWithExampleTrace,
} from "./_shared.js";

const workflowName = "TypeScript Azure OpenAI Embeddings Example";

export async function embeddingsExample(): Promise<void> {
  const respan = await createRespan(
    "typescript-azure-openai-embeddings-example",
  );
  await respan.initialize();

  try {
    const result = await runWithExampleTrace(respan, workflowName, async () => {
      const client = createAzureClient("text-embedding-3-small");
      return await client.embeddings.create({
        model: "text-embedding-3-small",
        input: [
          "Respan captures Azure OpenAI embedding calls.",
          "Returned vectors are captured in the canonical embedding output.",
        ],
      });
    });

    logExampleResult(workflowName, {
      embeddingCount: result.data.length,
      vectorDimensions: result.data[0]?.embedding.length,
      model: result.model,
    });
  } finally {
    await respan.shutdown();
  }
}

await embeddingsExample();
