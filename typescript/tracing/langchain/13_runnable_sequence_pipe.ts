import { RunnableLambda, RunnableSequence } from "@langchain/core/runnables";

import { initRespan, shutdown, tracingConfig } from "./_shared";

export async function runnableSequencePipe(): Promise<void> {
  const runtime = await initRespan(
    "typescript-langchain-runnable-sequence-pipe",
  );
  const addTopic = RunnableLambda.from((topic: string) => ({
    topic,
    fullTopic: `${topic} instrumentation`,
  }));
  const summarize = RunnableLambda.from(
    (input: { fullTopic: string }) => `Summary for ${input.fullTopic}`,
  );
  const sequence = RunnableSequence.from([addTopic, summarize]);

  try {
    const result = await sequence.invoke(
      "LangChain",
      tracingConfig(runtime, "runnable_sequence_pipe"),
    );
    console.log(result);
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await runnableSequencePipe();
}
