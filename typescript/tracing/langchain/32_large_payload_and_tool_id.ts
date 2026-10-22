import { HumanMessage } from "@langchain/core/messages";
import {
  chatModel,
  getWeather,
  initRespan,
  shutdown,
  tracingConfig,
} from "./_shared";

export async function largePayloadAndToolId(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-large-payload");
  const calls = [
    { id: "call_large_weather", name: "get_weather", args: { city: "Berlin" } },
  ];
  const model = chatModel([{ toolCalls: calls }]);
  const tools = Array.from({ length: 80 }, (_, index) => ({
    type: "function" as const,
    function: {
      name: index === 0 ? "get_weather" : `tool_${index}`,
      description: "Controlled tool definition.",
      parameters: { type: "object", properties: { city: { type: "string" } } },
    },
  }));
  const messages = Array.from(
    { length: 80 },
    (_, index) =>
      new HumanMessage(
        index === 79
          ? [
              { type: "text", text: "What is the weather in Berlin?" },
              {
                type: "image_url",
                image_url: { url: "data:image/png;base64,AAAA" },
              },
            ]
          : `Context message ${index}.`,
      ),
  );
  try {
    const response = await model
      .bindTools(tools)
      .invoke(messages, tracingConfig(runtime, "large_model"));
    const call = response.tool_calls?.[0];
    if (!call) throw new Error("Native response did not expose its tool call.");
    await getWeather.invoke(
      { ...call, type: "tool_call" },
      tracingConfig(runtime, "actual_tool_execution"),
    );
    console.log(
      `Preserved ${messages.length} messages, ${tools.length} definitions, and ${call.id}.`,
    );
  } finally {
    await shutdown(runtime);
  }
}
if (import.meta.url === `file://${process.argv[1]}`)
  await largePayloadAndToolId();
