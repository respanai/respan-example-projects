import { MODEL, createRuntime, runCase, log, toolInput } from "./_shared.js";
const caseId = "tool";
const runtime = await createRuntime();
try {
  const result = await runCase(runtime.respan, caseId, async () => {
    const tools = [
      {
        name: "lookup_weather",
        description: "Get controlled weather data.",
        input_schema: {
          type: "object" as const,
          properties: {
            enabled: { type: "boolean" },
            count: { type: "number" },
          },
          required: [],
        },
      },
    ];
    const first = await runtime.client.messages.create({
      model: MODEL,
      max_tokens: 512,
      tools,
      tool_choice: { type: "tool", name: "lookup_weather" },
      messages: [{ role: "user", content: "Call the weather tool." }],
    });
    const call = first.content.find((block) => block.type === "tool_use");
    if (!call || call.type !== "tool_use")
      throw Error("Missing native tool call");
    const output = await runtime.respan.withTool({ name: call.name }, () => {
      toolInput(call.name, call.id, call.input);
      return { enabled: false, count: 0, empty: "", nil: null };
    });
    const final = await runtime.client.messages.create({
      model: MODEL,
      max_tokens: 512,
      tools,
      messages: [
        { role: "user", content: "Call the weather tool." },
        { role: "assistant", content: first.content },
        {
          role: "user",
          content: [
            {
              type: "tool_result",
              tool_use_id: call.id,
              content: JSON.stringify(output),
            },
          ],
        },
      ],
    });
    return { toolCallId: call.id, blocks: final.content.length };
  });
  log(caseId, result);
} finally {
  await runtime.close(caseId);
}
