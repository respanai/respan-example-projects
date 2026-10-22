import { textModel, initRespan, shutdown, tracingConfig } from "./_shared";

export async function llmStream(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-llm-stream");
  const llm = textModel("Streaming from a string LLM.");

  try {
    const chunks = await llm.stream(
      "Stream a short string.",
      tracingConfig(runtime, "llm_stream"),
    );
    const parts: string[] = [];
    for await (const chunk of chunks) {
      parts.push(chunk);
    }
    console.log(parts.join(""));
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await llmStream();
}
