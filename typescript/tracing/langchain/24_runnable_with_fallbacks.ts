import { RunnableLambda } from "@langchain/core/runnables";

import { initRespan, shutdown, tracingConfig } from "./_shared";

export async function runnableWithFallbacks(): Promise<void> {
  const runtime = await initRespan(
    "typescript-langchain-runnable-with-fallbacks",
  );
  const primary = RunnableLambda.from<string, string>(() => {
    throw new Error("primary failed");
  });
  const fallback = RunnableLambda.from(
    (input: string) => `fallback handled ${input}`,
  );
  const runnable = primary.withFallbacks({ fallbacks: [fallback] });

  try {
    const result = await runnable.invoke(
      "request",
      tracingConfig(runtime, "runnable_with_fallbacks"),
    );
    console.log(result);
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await runnableWithFallbacks();
}
