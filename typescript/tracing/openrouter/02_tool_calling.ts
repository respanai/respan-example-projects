import {
  CHAT_MODEL,
  createOpenRouterClient,
  createRespan,
  logExampleResult,
  runWithOpenRouterWorkflow,
  shutdownRespan,
} from "./_shared.js";

type OpenRouterRespan = ReturnType<typeof createRespan>;

export async function runToolCalling(
  respan: OpenRouterRespan = createRespan(),
): Promise<unknown> {
  const workflowName = "openrouter_ts_tool_calling";
  const shouldShutdown = arguments.length === 0;
  try {
    const toolCalls = await runWithOpenRouterWorkflow(
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
                content:
                  "Use the provided tool when the user asks for shipping timing.",
              },
              {
                role: "user",
                content: "When will order OR-2048 arrive in Austin?",
              },
            ],
            tools: [
              {
                type: "function",
                function: {
                  name: "get_shipping_eta",
                  description:
                    "Return the estimated delivery date for an order.",
                  parameters: {
                    type: "object",
                    properties: {
                      order_id: { type: "string" },
                      destination: { type: "string" },
                    },
                    required: ["order_id", "destination"],
                  },
                },
              },
            ],
            toolChoice: "auto" as never,
            temperature: 0,
            maxTokens: 120,
          },
        });
        if (!("choices" in response)) {
          throw new Error(
            "Expected a non-streaming OpenRouter tool-call response.",
          );
        }
        return response.choices?.[0]?.message?.toolCalls;
      },
    );
    logExampleResult(workflowName, { model: CHAT_MODEL, toolCalls });
    return toolCalls;
  } finally {
    if (shouldShutdown) await shutdownRespan(respan);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runToolCalling().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
