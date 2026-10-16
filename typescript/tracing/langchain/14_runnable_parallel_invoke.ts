import { RunnableLambda, RunnableParallel } from "@langchain/core/runnables";

import { initRespan, shutdown, tracingConfig } from "./_shared";

export async function runnableParallelInvoke(): Promise<void> {
  const runtime = await initRespan(
    "typescript-langchain-runnable-parallel-invoke",
  );
  const parallel = RunnableParallel.from({
    upper: RunnableLambda.from((text: string) => text.toUpperCase()),
    length: RunnableLambda.from((text: string) => text.length),
  });

  try {
    const result = await parallel.invoke(
      "respan",
      tracingConfig(runtime, "runnable_parallel_invoke"),
    );
    console.log(JSON.stringify(result));
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await runnableParallelInvoke();
}
