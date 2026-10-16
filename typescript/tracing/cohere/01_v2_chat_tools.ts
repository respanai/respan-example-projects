import { logExampleResult, runCohereWorkflow } from "./_shared.js";

const workflowName = "cohere_ts_v2_chat_tools";

const result = await runCohereWorkflow(workflowName, async ({ clientV2 }) => {
  return clientV2.chat({
    model: "command-a-03-2025",
    messages: Array.from({ length: 80 }, (_, i) => ({
      role: "user" as const,
      content:
        i === 79
          ? [
              {
                type: "text" as const,
                text: "Use a tool to summarize Respan tracing.",
              },
              {
                type: "image_url" as const,
                imageUrl: { url: "https://example.invalid/image.png" },
              },
            ]
          : `Context ${i}`,
    })),
    tools: Array.from({ length: 80 }, (_, i) => ({
      type: "function" as const,
      function: {
        name: `lookup_docs_${i}`,
        description: "Lookup product documentation.",
        parameters: {
          type: "object",
          properties: {
            topic: { type: "string" },
            flag: { type: "boolean", default: false },
            value: { type: "number", default: 0 },
          },
          required: ["topic"],
        },
      },
    })),
  });
});

logExampleResult(workflowName, {
  content: result.message?.content,
  toolCalls: result.message?.toolCalls?.length ?? 0,
});
