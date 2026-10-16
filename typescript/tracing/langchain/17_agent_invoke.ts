import { createAgent } from "langchain";

import {
  chatModel,
  getWeather,
  initRespan,
  shutdown,
  tracingConfig,
} from "./_shared";

export async function agentInvoke(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-agent-invoke");
  const model = chatModel([
    {
      toolCalls: [
        {
          id: "call_weather",
          name: "get_weather",
          args: { city: "San Francisco" },
        },
      ],
    },
    "It is sunny in San Francisco.",
  ]);
  const agent = createAgent({ model, tools: [getWeather] });

  try {
    const result = await agent.invoke(
      { messages: [{ role: "user", content: "What is the weather in SF?" }] },
      tracingConfig(runtime, "agent_invoke", { framework: "langgraph" }),
    );
    console.log(result.messages.at(-1)?.content);
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await agentInvoke();
}
