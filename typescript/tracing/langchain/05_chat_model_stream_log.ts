import { chatModel, initRespan, shutdown, tracingConfig } from "./_shared";

export async function chatModelStreamLog(): Promise<void> {
  const runtime = await initRespan(
    "typescript-langchain-chat-model-stream-log",
  );
  const model = chatModel(["stream log response"]);

  try {
    const patches = model.streamLog(
      "Emit a runnable log.",
      tracingConfig(runtime, "chat_model_stream_log"),
    );
    let patchCount = 0;
    for await (const _patch of patches) {
      patchCount += 1;
    }
    console.log(`patches=${patchCount}`);
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await chatModelStreamLog();
}
