import { chatModel, initRespan, shutdown, tracingConfig } from "./_shared";

export async function llmError(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-llm-error");
  const model = chatModel([{ error: "llm failed" }]);

  try {
    await model.invoke(
      "fail this model call",
      tracingConfig(runtime, "llm_error"),
    );
  } catch (error) {
    console.log(`caught expected error: ${(error as Error).message}`);
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await llmError();
}
