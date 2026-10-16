import {
  createRespan,
  createWriterClient,
  DEFAULT_CHAT_MODEL,
  logExampleResult,
  runWithWriterWorkflow,
  shutdownRespan,
  withTimeout,
} from "./_shared.js";

const workflowName = "writer.streaming_chat.workflow";
const respan = createRespan();
const writer = createWriterClient();

try {
  const completion = await withTimeout(
    runWithWriterWorkflow(respan, workflowName, async () => {
      const runner = writer.chat.stream({
        model: DEFAULT_CHAT_MODEL,
        messages: [
          { role: "user", content: "Stream a short Writer tracing sentence." },
        ],
        stream_options: { include_usage: true },
      });
      return await runner.finalChatCompletion();
    }),
    workflowName,
  );

  logExampleResult(workflowName, {
    expected: "one streamed chat span with reconstructed output",
    actual: completion.choices[0]?.message?.content,
    usage: completion.usage,
  });
} finally {
  await shutdownRespan(respan);
}
