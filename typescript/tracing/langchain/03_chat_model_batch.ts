import {
  chatModel,
  initRespan,
  messageText,
  shutdown,
  tracingConfig,
} from "./_shared";

export async function chatModelBatch(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-chat-model-batch");
  const model = chatModel(["first batch response", "second batch response"]);

  try {
    const responses = await model.batch(
      ["First request", "Second request"],
      tracingConfig(runtime, "chat_model_batch"),
    );
    console.log(responses.map(messageText).join(" | "));
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await chatModelBatch();
}
