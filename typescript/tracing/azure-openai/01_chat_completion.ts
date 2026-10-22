import {
  createAzureClient,
  createRespan,
  logExampleResult,
  runWithExampleTrace,
} from "./_shared.js";

const workflowName = "TypeScript Azure OpenAI Chat Example";

export async function chatCompletionExample(): Promise<void> {
  const respan = await createRespan("typescript-azure-openai-chat-example");
  await respan.initialize();

  try {
    const result = await runWithExampleTrace(respan, workflowName, async () => {
      const client = createAzureClient("gpt-4o-mini");
      return await client.chat.completions.create({
        model: "gpt-4o-mini",
        messages: Array.from({ length: 76 }, (_, index) => ({
          role: "user" as const,
          content: `Context ${index}: explain why tracing Azure OpenAI requests is useful.`,
        })),
        tools: Array.from({ length: 76 }, (_, index) => ({
          type: "function" as const,
          function: {
            name: `lookup_${index}`,
            parameters: {
              type: "object",
              properties: { enabled: { type: "boolean", default: false } },
            },
          },
        })),
      });
    });

    logExampleResult(workflowName, {
      content: result.choices[0]?.message?.content,
      model: result.model,
    });
  } finally {
    await respan.shutdown();
  }
}

await chatCompletionExample();
