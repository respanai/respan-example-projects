import { createAgent } from "langchain";

import {
  chatModel,
  getWeather,
  initRespan,
  shutdown,
  tracingConfig,
} from "./_shared";

export async function agentStreamUpdates(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-agent-stream-updates");
  const model = chatModel([
    {
      toolCalls: [
        { id: "call_weather", name: "get_weather", args: { city: "Austin" } },
      ],
    },
    "It is sunny in Austin.",
  ]);
  const agent = createAgent({ model, tools: [getWeather] });

  try {
    const stream = await agent.stream(
      { messages: [{ role: "user", content: "Weather in Austin?" }] },
      {
        ...tracingConfig(runtime, "agent_stream_updates", {
          framework: "langgraph",
        }),
        streamMode: "updates",
      },
    );
    const chunks: string[] = [];
    for await (const chunk of stream) {
      chunks.push(Object.keys(chunk).join(","));
    }
    console.log(chunks.join(" -> "));
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await agentStreamUpdates();
}
