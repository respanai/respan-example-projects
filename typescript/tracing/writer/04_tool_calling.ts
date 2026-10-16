import {
  createRespan,
  createWriterClient,
  DEFAULT_CHAT_MODEL,
  logExampleResult,
  runWithWriterWorkflow,
  shutdownRespan,
  withTimeout,
} from "./_shared.js";

const workflowName = "writer.tool_calling.workflow";
const respan = createRespan();
const writer = createWriterClient();

function getWeather(args: { city: string }): {
  city: string;
  forecast: string;
  temperature_c: number;
} {
  return { city: args.city, forecast: "clear", temperature_c: 23 };
}

try {
  const finalCompletion = await withTimeout(
    runWithWriterWorkflow(respan, workflowName, async () => {
      const first = await writer.chat.chat({
        model: DEFAULT_CHAT_MODEL,
        messages: [
          {
            role: "user",
            content: "Use a tool to check the weather in Tokyo.",
          },
        ],
        tools: [
          {
            type: "function",
            function: {
              name: "get_weather",
              description: "Get the current weather for a city.",
              parameters: {
                type: "object",
                properties: { city: { type: "string" } },
                required: ["city"],
              },
            },
          },
        ],
        tool_choice: { value: "auto" },
      });

      const toolCall = first.choices[0]?.message?.tool_calls?.[0];
      if (!toolCall) {
        throw new Error("Writer did not return a tool call.");
      }

      const args = JSON.parse(toolCall.function.arguments || "{}") as {
        city: string;
      };
      const toolResult = await respan.withTool(
        { name: "get_weather" },
        async (input: { city: string }) => getWeather(input),
        args,
      );

      return await writer.chat.chat({
        model: DEFAULT_CHAT_MODEL,
        messages: [
          {
            role: "user",
            content: "Use a tool to check the weather in Tokyo.",
          },
          first.choices[0].message,
          {
            role: "tool",
            tool_call_id: toolCall.id,
            content: JSON.stringify(toolResult),
          },
        ],
      });
    }),
    workflowName,
  );

  logExampleResult(workflowName, {
    expected:
      "two chat spans plus the explicit withTool execution span; historical context adds no executions",
    actual: finalCompletion.choices[0]?.message?.content,
  });
} finally {
  await shutdownRespan(respan);
}
