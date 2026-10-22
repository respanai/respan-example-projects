import { chatModel, initRespan, shutdown, tracingConfig } from "./_shared";

export async function chatModelStreamEvents(): Promise<void> {
  const runtime = await initRespan(
    "typescript-langchain-chat-model-stream-events",
  );
  const model = chatModel(["stream events response"]);

  try {
    const events = model.streamEvents("Emit callback events.", {
      ...tracingConfig(runtime, "chat_model_stream_events"),
      version: "v2",
    });
    const names: string[] = [];
    for await (const event of events) {
      names.push(event.event);
    }
    console.log(names.join(" -> "));
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await chatModelStreamEvents();
}
