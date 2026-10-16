import {
  EMBEDDING_MODEL,
  createOpenRouterClient,
  createRespan,
  logExampleResult,
  runWithOpenRouterWorkflow,
  shutdownRespan,
} from "./_shared.js";

type OpenRouterRespan = ReturnType<typeof createRespan>;

export async function runEmbeddings(
  respan: OpenRouterRespan = createRespan(),
): Promise<number | undefined> {
  const workflowName = "openrouter_ts_embeddings";
  const shouldShutdown = arguments.length === 0;
  try {
    const vectorCount = await runWithOpenRouterWorkflow(
      respan,
      workflowName,
      async () => {
        const client = createOpenRouterClient();
        const response = await client.embeddings.generate({
          requestBody: {
            model: EMBEDDING_MODEL,
            input: [
              "Respan captures traces for OpenRouter TypeScript applications.",
              "Embedding spans preserve vector output for observability.",
            ],
          },
        });
        if (typeof response === "string") {
          throw new Error(
            "Expected a structured OpenRouter embeddings response.",
          );
        }
        return response.data?.length;
      },
    );
    logExampleResult(workflowName, { model: EMBEDDING_MODEL, vectorCount });
    return vectorCount;
  } finally {
    if (shouldShutdown) await shutdownRespan(respan);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runEmbeddings().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
