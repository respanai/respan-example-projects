import {
  createRespan,
  createWriterClient,
  DEFAULT_CHAT_MODEL,
  logExampleResult,
  runWithWriterWorkflow,
  shutdownRespan,
} from "./_shared.js";
const respan = createRespan(),
  writer = createWriterClient(),
  workflowName = "writer.history_schema.workflow";
try {
  await runWithWriterWorkflow(respan, workflowName, async () => {
    const messages = Array.from({ length: 75 }, (_, i) => ({
      role: "user" as const,
      content: `Controlled historical message ${i}`,
    }));
    const schema = {
      type: "object",
      properties: Object.fromEntries(
        Array.from({ length: 75 }, (_, i) => [
          `field_${i}`,
          { type: "string", description: `Controlled schema field ${i}` },
        ]),
      ),
    };
    const result = await writer.chat.chat({
      model: DEFAULT_CHAT_MODEL,
      messages,
      tools: [
        {
          type: "function",
          function: {
            name: "full_schema",
            description: "Preserve every schema property",
            parameters: schema,
          },
        },
      ],
      temperature: 0,
    });
    logExampleResult(workflowName, {
      expected:
        "all 75 messages and schema properties; only current output tools",
      messages: messages.length,
      properties: Object.keys(schema.properties).length,
      toolId: result.choices[0]?.message.tool_calls?.[0]?.id,
    });
  });
} finally {
  await shutdownRespan(respan);
}
