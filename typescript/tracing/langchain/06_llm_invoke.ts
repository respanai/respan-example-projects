import { textModel, initRespan, shutdown, tracingConfig } from "./_shared";

export async function llmInvoke(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-llm-invoke");
  const llm = textModel("Legacy string LLM response.");

  try {
    const response = await llm.invoke(
      "Say hello as a string LLM.",
      tracingConfig(runtime, "llm_invoke"),
    );
    console.log(response);
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await llmInvoke();
}
