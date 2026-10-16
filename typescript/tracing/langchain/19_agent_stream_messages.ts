import { createAgent } from "langchain";

import {
  chatModel,
  initRespan,
  messageText,
  shutdown,
  tracingConfig,
} from "./_shared";

export async function agentStreamMessages(): Promise<void> {
  const runtime = await initRespan(
    "typescript-langchain-agent-stream-messages",
  );
  const model = chatModel(["Streaming message response."]);
  const agent = createAgent({ model, tools: [] });

  try {
    const stream = await agent.stream(
      { messages: [{ role: "user", content: "Reply briefly." }] },
      {
        ...tracingConfig(runtime, "agent_stream_messages", {
          framework: "langgraph",
        }),
        streamMode: "messages",
      },
    );
    const chunks: string[] = [];
    for await (const [token] of stream) {
      chunks.push(messageText(token));
    }
    console.log(chunks.join(""));
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await agentStreamMessages();
}
