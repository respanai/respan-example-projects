import {
  chatModel,
  getWeather,
  initRespan,
  messageText,
  shutdown,
  tracingConfig,
} from "./_shared";

export async function modelBindTools(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-model-bind-tools");
  const model = chatModel([
    {
      toolCalls: [
        { id: "call_weather", name: "get_weather", args: { city: "Berlin" } },
      ],
    },
  ]);
  const modelWithTools = model.bindTools([getWeather]);

  try {
    const response = await modelWithTools.invoke(
      "What is the weather in Berlin?",
      tracingConfig(runtime, "model_bind_tools"),
    );
    console.log(messageText(response));
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await modelBindTools();
}
