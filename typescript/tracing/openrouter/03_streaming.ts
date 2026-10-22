import {
  CHAT_MODEL,
  createOpenRouterClient,
  createRespan,
  logExampleResult,
  runWithOpenRouterWorkflow,
  shutdownRespan,
} from "./_shared.js";

type OpenRouterRespan = ReturnType<typeof createRespan>;

export async function runStreaming(
  respan: OpenRouterRespan = createRespan(),
): Promise<string> {
  const workflowName = "openrouter_ts_streaming";
  const shouldShutdown = arguments.length === 0;
  try {
    const content = await runWithOpenRouterWorkflow(
      respan,
      workflowName,
      async () => {
        const client = createOpenRouterClient();
        const stream = await client.chat.send({
          chatRequest: {
            model: CHAT_MODEL,
            messages: [
              { role: "system", content: "You answer with concise prose." },
              {
                role: "user",
                content:
                  "Stream a one-sentence explanation of why tracing matters.",
              },
            ],
            stream: true,
            streamOptions: { includeUsage: true },
            temperature: 0,
            maxTokens: 90,
          },
        });

        let text = "";
        for await (const chunk of stream as AsyncIterable<any>) {
          text += chunk.choices?.[0]?.delta?.content ?? "";
        }
        return text;
      },
    );
    logExampleResult(workflowName, { model: CHAT_MODEL, content });
    return content;
  } finally {
    if (shouldShutdown) await shutdownRespan(respan);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runStreaming().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
