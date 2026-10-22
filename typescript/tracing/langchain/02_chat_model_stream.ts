import {
  chatModel,
  initRespan,
  messageText,
  shutdown,
  tracingConfig,
} from "./_shared";

export async function chatModelStream(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-chat-model-stream");
  const model = chatModel(["Streaming hello from LangChain."]);

  try {
    const chunks = await model.stream(
      "Stream a short hello.",
      tracingConfig(runtime, "chat_model_stream"),
    );
    const parts: string[] = [];
    for await (const chunk of chunks) {
      parts.push(messageText(chunk));
    }
    console.log(parts.join(""));
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await chatModelStream();
}
