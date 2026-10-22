import {
  CHAT_MODEL,
  createOpenRouterClient,
  createRespan,
  logExampleResult,
  runWithOpenRouterWorkflow,
  shutdownRespan,
} from "./_shared.js";

type OpenRouterRespan = ReturnType<typeof createRespan>;

export async function runChatCompletion(
  respan: OpenRouterRespan = createRespan(),
): Promise<unknown> {
  const workflowName = "openrouter_ts_chat_completion";
  const shouldShutdown = arguments.length === 0;
  try {
    const content = await runWithOpenRouterWorkflow(
      respan,
      workflowName,
      async () => {
        const client = createOpenRouterClient();
        const response = await client.chat.send({
          chatRequest: {
            model: CHAT_MODEL,
            messages: [
              {
                role: "system",
                content: "You answer with short, concrete responses.",
              },
              {
                role: "user",
                content:
                  "Say hello from OpenRouter and Respan in one sentence.",
              },
            ],
            temperature: 0,
            maxTokens: 80,
          },
        });
        if (!("choices" in response)) {
          throw new Error("Expected a non-streaming OpenRouter chat response.");
        }
        return response.choices?.[0]?.message?.content;
      },
    );
    logExampleResult(workflowName, { model: CHAT_MODEL, content });
    return content;
  } finally {
    if (shouldShutdown) await shutdownRespan(respan);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runChatCompletion().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
