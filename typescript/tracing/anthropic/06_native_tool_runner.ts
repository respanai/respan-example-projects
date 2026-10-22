import { MODEL, createRuntime, runCase, log } from "./_shared.js";
const caseId = "native_tool_runner";
const runtime = await createRuntime();
try {
  const result = await runCase(runtime.respan, caseId, async () => {
    let calls = 0,
      toolCallId: string | undefined;
    const runner = runtime.client.beta.messages.toolRunner({
      model: MODEL,
      max_tokens: 512,
      max_iterations: 3,
      messages: [
        { role: "user", content: "Use the native runnable tool once." },
      ],
      tools: [
        {
          name: "lookup_native",
          description: "Return controlled scalar data.",
          input_schema: {
            type: "object",
            properties: {
              enabled: { type: "boolean" },
              count: { type: "number" },
            },
            required: [],
          },
          parse: (input: unknown) => input,
          run: async (input: unknown, context) => {
            calls++;
            toolCallId = context?.toolUse.id;
            return JSON.stringify(input);
          },
        },
      ],
    });
    const final = await runner.runUntilDone();
    return { calls, toolCallId, finalBlocks: final.content.length };
  });
  log(caseId, result);
} finally {
  await runtime.close(caseId);
}
