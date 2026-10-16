import { createAgent, tool } from "langchain";
import { z } from "zod";

import { chatModel, initRespan, shutdown, tracingConfig } from "./_shared";

const getWeatherWithProgress = tool(
  async (
    { city }: { city: string },
    config: { writer?: ((chunk: unknown) => void) | null },
  ) => {
    config.writer?.(`Looking up weather for ${city}`);
    config.writer?.(`Finished weather lookup for ${city}`);
    return `It is sunny in ${city}.`;
  },
  {
    name: "get_weather_with_progress",
    description: "Get weather and stream progress updates.",
    schema: z.object({ city: z.string() }),
  },
);

export async function agentStreamCustom(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-agent-stream-custom");
  const model = chatModel([
    {
      toolCalls: [
        {
          id: "call_weather_progress",
          name: "get_weather_with_progress",
          args: { city: "Seattle" },
        },
      ],
    },
    "It is sunny in Seattle.",
  ]);
  const agent = createAgent({ model, tools: [getWeatherWithProgress] });

  try {
    const stream = await agent.stream(
      { messages: [{ role: "user", content: "Weather in Seattle?" }] },
      {
        ...tracingConfig(runtime, "agent_stream_custom", {
          framework: "langgraph",
        }),
        streamMode: "custom",
      },
    );
    const chunks: string[] = [];
    for await (const chunk of stream) {
      chunks.push(String(chunk));
    }
    console.log(chunks.join(" | "));
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await agentStreamCustom();
}
